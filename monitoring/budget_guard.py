#!/usr/bin/env python3
"""
monitoring/budget_guard.py
Enterprise Budget Guard System for Secure PR Guard
Real-time cost monitoring with intelligent alerting via Slack, Email, and Console
"""

import os
import csv
import json
import time
import yaml
import smtplib
import requests
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# OpenTelemetry imports for integration
from opentelemetry import trace
from opentelemetry.trace import get_current_span, Status, StatusCode

# Load environment variables
load_dotenv()

@dataclass
class AlertConfig:
    """Configuration for budget alerts"""
    daily_limit: float = 10.0          # USD daily limit
    hourly_limit: float = 2.0          # USD hourly limit  
    spike_threshold: float = 5.0       # Multiplier for spike detection
    efficiency_min: float = 0.10       # Minimum efficiency ($0.10/1K tokens)
    consecutive_violations: int = 3     # Alerts after N consecutive violations
    cooldown_minutes: int = 30         # Cooldown between same alert types
    
    # Alert channels
    slack_enabled: bool = True
    email_enabled: bool = True
    console_enabled: bool = True
    
    # Thresholds for different alert levels
    warning_threshold: float = 0.7     # 70% of limit
    critical_threshold: float = 0.9    # 90% of limit

@dataclass  
class Alert:
    """Alert data structure"""
    timestamp: datetime
    alert_type: str
    severity: str  # 'info', 'warning', 'critical'
    message: str
    current_value: float
    threshold: float
    pr_url: Optional[str] = None
    operation: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat()
        }

class BudgetGuard:
    """
    Enterprise Budget Guard System
    
    Features:
    - Real-time cost monitoring with configurable thresholds
    - Multi-channel alerting (Slack, Email, Console)
    - Intelligent spike detection and trend analysis
    - Integration with existing cost_logger.py
    - OpenTelemetry instrumentation for enterprise monitoring
    """
    
    def __init__(self, config_path: str = "monitoring/budget_config.yaml", 
                 csv_path: str = "logs/cost.csv"):
        self.config_path = Path(config_path)
        self.csv_path = Path(csv_path)
        self.alert_log_path = Path("logs/budget_alerts.json")
        
        # Load configuration
        self.config = self._load_config()
        
        # Alert tracking
        self.alerts_history: List[Alert] = []
        self.last_alert_time: Dict[str, datetime] = {}
        self.violation_count: Dict[str, int] = {}
        
        # Performance tracking
        self.baseline_metrics: Dict[str, float] = {}
        
        # Load alert history
        self._load_alert_history()
        
        # Initialize baseline metrics
        self._calculate_baseline_metrics()
        
        print("🛡️ Budget Guard initialized with intelligent monitoring")
    
    def _load_config(self) -> AlertConfig:
        """Load configuration from YAML file or create default"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                    return AlertConfig(**config_data)
            else:
                # Create default config
                default_config = AlertConfig()
                self._save_config(default_config)
                print(f"📝 Created default budget config: {self.config_path}")
                return default_config
                
        except Exception as e:
            print(f"⚠️ Config load error: {e}. Using defaults.")
            return AlertConfig()
    
    def _save_config(self, config: AlertConfig) -> None:
        """Save configuration to YAML file"""
        try:
            self.config_path.parent.mkdir(exist_ok=True)
            with open(self.config_path, 'w') as f:
                yaml.dump(asdict(config), f, default_flow_style=False, indent=2)
        except Exception as e:
            print(f"❌ Config save error: {e}")
    
    def _load_alert_history(self) -> None:
        """Load alert history from JSON file"""
        try:
            if self.alert_log_path.exists():
                with open(self.alert_log_path, 'r') as f:
                    alerts_data = json.load(f)
                    self.alerts_history = [
                        Alert(
                            timestamp=datetime.fromisoformat(alert['timestamp']),
                            alert_type=alert['alert_type'],
                            severity=alert['severity'],
                            message=alert['message'],
                            current_value=alert['current_value'],
                            threshold=alert['threshold'],
                            pr_url=alert.get('pr_url'),
                            operation=alert.get('operation')
                        )
                        for alert in alerts_data
                    ]
                    print(f"📚 Loaded {len(self.alerts_history)} historical alerts")
        except Exception as e:
            print(f"⚠️ Alert history load error: {e}")
            self.alerts_history = []
    
    def _save_alert_history(self) -> None:
        """Save alert history to JSON file"""
        try:
            self.alert_log_path.parent.mkdir(exist_ok=True)
            # Keep only last 1000 alerts to prevent file bloat
            recent_alerts = self.alerts_history[-1000:]
            
            with open(self.alert_log_path, 'w') as f:
                json.dump([alert.to_dict() for alert in recent_alerts], f, indent=2)
                
        except Exception as e:
            print(f"❌ Alert history save error: {e}")
    
    def _calculate_baseline_metrics(self) -> None:
        """Calculate baseline performance metrics from historical data"""
        try:
            if not self.csv_path.exists():
                self.baseline_metrics = {
                    'avg_cost_per_operation': 0.001,
                    'avg_latency_ms': 5000,
                    'avg_cost_per_1k_tokens': 0.15
                }
                return
            
            # Load recent data (last 7 days)
            df = pd.read_csv(self.csv_path)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
            
            # Filter to last 7 days
            cutoff = pd.Timestamp.now() - timedelta(days=7)
            df = df[df['timestamp'] >= cutoff]
            
            if len(df) > 0:
                df['cost_per_1k_tokens'] = (df['cost_usd'] / df['total_tokens']) * 1000
                
                self.baseline_metrics = {
                    'avg_cost_per_operation': df['cost_usd'].mean(),
                    'avg_latency_ms': df['latency_ms'].mean(),
                    'avg_cost_per_1k_tokens': df['cost_per_1k_tokens'].mean(),
                    'p95_cost': df['cost_usd'].quantile(0.95),
                    'p95_latency': df['latency_ms'].quantile(0.95)
                }
                
                print(f"📊 Baseline metrics calculated from {len(df)} operations")
            else:
                # Fallback defaults
                self.baseline_metrics = {
                    'avg_cost_per_operation': 0.001,
                    'avg_latency_ms': 5000,
                    'avg_cost_per_1k_tokens': 0.15,
                    'p95_cost': 0.01,
                    'p95_latency': 10000
                }
                
        except Exception as e:
            print(f"⚠️ Baseline calculation error: {e}")
            self.baseline_metrics = {}
    
    def check_budget_limits(self, pr_url: str = None, operation: str = None) -> List[Alert]:
        """
        Check all budget limits and return any violations
        
        Args:
            pr_url: Current PR being processed (for context)
            operation: Current operation (for context)
            
        Returns:
            List of Alert objects for any violations
        """
        alerts = []
        
        try:
            if not self.csv_path.exists():
                return alerts
            
            # Load recent data
            df = pd.read_csv(self.csv_path)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
            df = df.dropna(subset=['timestamp', 'cost_usd'])
            
            current_time = pd.Timestamp.now()
            
            # Check hourly limit
            hourly_cutoff = current_time - timedelta(hours=1)
            hourly_data = df[df['timestamp'] >= hourly_cutoff]
            hourly_cost = hourly_data['cost_usd'].sum()
            
            alerts.extend(self._check_threshold(
                value=hourly_cost,
                limit=self.config.hourly_limit,
                alert_type='hourly_budget',
                message_template="Hourly budget limit approached: ${:.4f} / ${:.4f}",
                pr_url=pr_url,
                operation=operation
            ))
            
            # Check daily limit
            daily_cutoff = current_time - timedelta(days=1)
            daily_data = df[df['timestamp'] >= daily_cutoff]
            daily_cost = daily_data['cost_usd'].sum()
            
            alerts.extend(self._check_threshold(
                value=daily_cost,
                limit=self.config.daily_limit,
                alert_type='daily_budget',
                message_template="Daily budget limit approached: ${:.4f} / ${:.4f}",
                pr_url=pr_url,
                operation=operation
            ))
            
            # Check cost spike (last 5 operations vs baseline)
            if len(df) >= 5:
                recent_avg = df.tail(5)['cost_usd'].mean()
                baseline_avg = self.baseline_metrics.get('avg_cost_per_operation', 0.001)
                spike_threshold = baseline_avg * self.config.spike_threshold
                
                if recent_avg > spike_threshold:
                    alerts.append(Alert(
                        timestamp=current_time.to_pydatetime(),
                        alert_type='cost_spike',
                        severity='warning',
                        message=f"Cost spike detected: ${recent_avg:.4f} avg (>{self.config.spike_threshold}x baseline)",
                        current_value=recent_avg,
                        threshold=spike_threshold,
                        pr_url=pr_url,
                        operation=operation
                    ))
            
            # Check efficiency degradation
            if len(daily_data) > 0:
                daily_data['cost_per_1k_tokens'] = (daily_data['cost_usd'] / daily_data['total_tokens']) * 1000
                avg_efficiency = daily_data['cost_per_1k_tokens'].mean()
                
                if avg_efficiency > self.config.efficiency_min:
                    alerts.append(Alert(
                        timestamp=current_time.to_pydatetime(),
                        alert_type='efficiency_degradation',
                        severity='info' if avg_efficiency < self.config.efficiency_min * 1.5 else 'warning',
                        message=f"Efficiency concern: ${avg_efficiency:.4f}/1K tokens (target: ${self.config.efficiency_min:.4f})",
                        current_value=avg_efficiency,
                        threshold=self.config.efficiency_min,
                        pr_url=pr_url,
                        operation=operation
                    ))
            
            # Process and send alerts
            for alert in alerts:
                self._process_alert(alert)
            
            return alerts
            
        except Exception as e:
            print(f"❌ Budget check error: {e}")
            return []
    
    def _check_threshold(self, value: float, limit: float, alert_type: str, 
                        message_template: str, pr_url: str = None, 
                        operation: str = None) -> List[Alert]:
        """Check a specific threshold and generate appropriate alerts"""
        alerts = []
        current_time = datetime.now()
        
        # Calculate threshold percentages
        warning_threshold = limit * self.config.warning_threshold
        critical_threshold = limit * self.config.critical_threshold
        
        if value >= critical_threshold:
            severity = 'critical'
            message = message_template.format(value, limit) + " [CRITICAL]"
        elif value >= warning_threshold:
            severity = 'warning' 
            message = message_template.format(value, limit) + " [WARNING]"
        else:
            return alerts  # No alert needed
        
        # Check cooldown
        last_alert = self.last_alert_time.get(alert_type)
        if last_alert and (current_time - last_alert).total_seconds() < (self.config.cooldown_minutes * 60):
            return alerts  # Still in cooldown
        
        alert = Alert(
            timestamp=current_time,
            alert_type=alert_type,
            severity=severity,
            message=message,
            current_value=value,
            threshold=limit,
            pr_url=pr_url,
            operation=operation
        )
        
        alerts.append(alert)
        return alerts
    
    def _process_alert(self, alert: Alert) -> None:
        """Process and send an alert through configured channels"""
        try:
            # Update tracking
            self.alerts_history.append(alert)
            self.last_alert_time[alert.alert_type] = alert.timestamp
            
            # Increment violation count
            self.violation_count[alert.alert_type] = self.violation_count.get(alert.alert_type, 0) + 1
            
            # Send through configured channels
            if self.config.console_enabled:
                self._send_console_alert(alert)
            
            if self.config.slack_enabled:
                self._send_slack_alert(alert)
            
            if self.config.email_enabled:
                self._send_email_alert(alert)
            
            # Update OpenTelemetry span
            self._record_alert_telemetry(alert)
            
            # Save alert history
            self._save_alert_history()
            
        except Exception as e:
            print(f"❌ Alert processing error: {e}")
    
    def _send_console_alert(self, alert: Alert) -> None:
        """Send alert to console with color coding"""
        emoji_map = {
            'info': 'ℹ️',
            'warning': '⚠️', 
            'critical': '🚨'
        }
        
        emoji = emoji_map.get(alert.severity, 'ℹ️')
        timestamp = alert.timestamp.strftime('%H:%M:%S')
        
        print(f"\n{emoji} BUDGET ALERT [{alert.severity.upper()}] - {timestamp}")
        print(f"   Type: {alert.alert_type}")
        print(f"   Message: {alert.message}")
        
        if alert.pr_url:
            print(f"   PR: {alert.pr_url}")
        if alert.operation:
            print(f"   Operation: {alert.operation}")
            
        print(f"   Current: {alert.current_value:.4f} | Threshold: {alert.threshold:.4f}")
        print("-" * 50)
    
    def _send_slack_alert(self, alert: Alert) -> None:
        """Send alert to Slack webhook"""
        try:
            webhook_url = os.getenv('SLACK_WEBHOOK_URL')
            if not webhook_url:
                print("⚠️ Slack webhook URL not configured")
                return
            
            # Color coding for Slack
            color_map = {
                'info': '#36a64f',     # Green
                'warning': '#ff9900',  # Orange  
                'critical': '#d93025'  # Red
            }
            
            # Create rich Slack message
            slack_payload = {
                "text": f"🛡️ Budget Alert: {alert.alert_type}",
                "attachments": [
                    {
                        "color": color_map.get(alert.severity, '#36a64f'),
                        "fields": [
                            {
                                "title": "Alert Type",
                                "value": alert.alert_type.replace('_', ' ').title(),
                                "short": True
                            },
                            {
                                "title": "Severity",
                                "value": alert.severity.upper(),
                                "short": True
                            },
                            {
                                "title": "Current Value",
                                "value": f"${alert.current_value:.4f}",
                                "short": True
                            },
                            {
                                "title": "Threshold",
                                "value": f"${alert.threshold:.4f}",
                                "short": True
                            },
                            {
                                "title": "Message",
                                "value": alert.message,
                                "short": False
                            }
                        ],
                        "footer": "Secure PR Guard Budget Monitor",
                        "ts": int(alert.timestamp.timestamp())
                    }
                ]
            }
            
            # Add PR context if available
            if alert.pr_url:
                slack_payload["attachments"][0]["fields"].append({
                    "title": "PR URL",
                    "value": f"<{alert.pr_url}|View PR>",
                    "short": False
                })
            
            response = requests.post(webhook_url, json=slack_payload, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ Slack alert sent: {alert.alert_type}")
            else:
                print(f"❌ Slack alert failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Slack alert error: {e}")
    
    def _send_email_alert(self, alert: Alert) -> None:
        """Send alert via email"""
        try:
            # Email configuration from environment
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            email_user = os.getenv('EMAIL_USER')
            email_password = os.getenv('EMAIL_PASSWORD')
            email_recipients = os.getenv('EMAIL_RECIPIENTS', '').split(',')
            
            if not all([email_user, email_password, email_recipients[0]]):
                print("⚠️ Email configuration incomplete")
                return
            
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🛡️ Budget Alert: {alert.alert_type} [{alert.severity.upper()}]"
            msg['From'] = email_user
            msg['To'] = ', '.join(email_recipients)
            
            # HTML email body
            html_body = f"""
            <html>
              <body style="font-family: Arial, sans-serif;">
                <h2 style="color: {'#d93025' if alert.severity == 'critical' else '#ff9900' if alert.severity == 'warning' else '#36a64f'};">
                  🛡️ Secure PR Guard Budget Alert
                </h2>
                
                <table style="border-collapse: collapse; width: 100%;">
                  <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Alert Type:</strong></td>
                      <td style="padding: 8px; border: 1px solid #ddd;">{alert.alert_type.replace('_', ' ').title()}</td></tr>
                  <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Severity:</strong></td>
                      <td style="padding: 8px; border: 1px solid #ddd;">{alert.severity.upper()}</td></tr>
                  <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Message:</strong></td>
                      <td style="padding: 8px; border: 1px solid #ddd;">{alert.message}</td></tr>
                  <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Current Value:</strong></td>
                      <td style="padding: 8px; border: 1px solid #ddd;">${alert.current_value:.4f}</td></tr>
                  <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Threshold:</strong></td>
                      <td style="padding: 8px; border: 1px solid #ddd;">${alert.threshold:.4f}</td></tr>
                  <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Timestamp:</strong></td>
                      <td style="padding: 8px; border: 1px solid #ddd;">{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
            """
            
            if alert.pr_url:
                html_body += f"""
                  <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>PR URL:</strong></td>
                      <td style="padding: 8px; border: 1px solid #ddd;"><a href="{alert.pr_url}">{alert.pr_url}</a></td></tr>
                """
            
            html_body += """
                </table>
                
                <p style="margin-top: 20px; color: #666;">
                  This alert was generated by Secure PR Guard Budget Monitor.<br>
                  Review your budget configuration in <code>monitoring/budget_config.yaml</code>
                </p>
              </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(email_user, email_password)
                server.send_message(msg)
            
            print(f"✅ Email alert sent: {alert.alert_type}")
            
        except Exception as e:
            print(f"❌ Email alert error: {e}")
    
    def _record_alert_telemetry(self, alert: Alert) -> None:
        """Record alert in OpenTelemetry for enterprise monitoring"""
        try:
            span = get_current_span()
            if span and span.is_recording():
                # Record alert attributes
                span.set_attributes({
                    "budget.alert.type": alert.alert_type,
                    "budget.alert.severity": alert.severity,
                    "budget.alert.current_value": alert.current_value,
                    "budget.alert.threshold": alert.threshold,
                    "budget.violation_count": self.violation_count.get(alert.alert_type, 0),
                })
                
                # Add alert event
                span.add_event("budget_alert_triggered", {
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "message": alert.message[:100],  # Truncate for telemetry
                    "current_value": alert.current_value,
                    "threshold": alert.threshold
                })
                
                # Set span status based on severity
                if alert.severity == 'critical':
                    span.set_status(Status(StatusCode.ERROR, f"Critical budget alert: {alert.alert_type}"))
                else:
                    span.set_status(Status(StatusCode.OK, f"Budget alert: {alert.alert_type}"))
                    
        except Exception as e:
            print(f"⚠️ Telemetry recording error: {e}")
    
    def get_budget_status(self) -> Dict[str, Any]:
        """Get current budget status and recent alerts"""
        try:
            if not self.csv_path.exists():
                return {"status": "no_data", "message": "No cost data available"}
            
            # Load recent data
            df = pd.read_csv(self.csv_path)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
            df = df.dropna(subset=['timestamp', 'cost_usd'])
            
            current_time = pd.Timestamp.now()
            
            # Calculate current usage
            hourly_cutoff = current_time - timedelta(hours=1)
            daily_cutoff = current_time - timedelta(days=1)
            
            hourly_cost = df[df['timestamp'] >= hourly_cutoff]['cost_usd'].sum()
            daily_cost = df[df['timestamp'] >= daily_cutoff]['cost_usd'].sum()
            
            # Recent alerts (last 24 hours)
            recent_alerts = [
                alert for alert in self.alerts_history 
                if alert.timestamp >= (current_time - timedelta(days=1)).to_pydatetime()
            ]
            
            return {
                "status": "active",
                "hourly_usage": {
                    "current": hourly_cost,
                    "limit": self.config.hourly_limit,
                    "percentage": (hourly_cost / self.config.hourly_limit) * 100 if self.config.hourly_limit > 0 else 0
                },
                "daily_usage": {
                    "current": daily_cost,
                    "limit": self.config.daily_limit,
                    "percentage": (daily_cost / self.config.daily_limit) * 100 if self.config.daily_limit > 0 else 0
                },
                "recent_alerts": len(recent_alerts),
                "alert_breakdown": {
                    "critical": len([a for a in recent_alerts if a.severity == 'critical']),
                    "warning": len([a for a in recent_alerts if a.severity == 'warning']),
                    "info": len([a for a in recent_alerts if a.severity == 'info'])
                },
                "baseline_metrics": self.baseline_metrics,
                "last_check": current_time.isoformat()
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def generate_budget_report(self) -> str:
        """Generate comprehensive budget report"""
        status = self.get_budget_status()
        
        if status["status"] != "active":
            return f"📊 Budget Report: {status.get('message', 'Unknown status')}"
        
        report = f"""
🛡️ SECURE PR GUARD - BUDGET STATUS REPORT
==========================================
📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

💰 CURRENT USAGE:
   Hourly: ${status['hourly_usage']['current']:.4f} / ${status['hourly_usage']['limit']:.2f} ({status['hourly_usage']['percentage']:.1f}%)
   Daily:  ${status['daily_usage']['current']:.4f} / ${status['daily_usage']['limit']:.2f} ({status['daily_usage']['percentage']:.1f}%)

🚨 RECENT ALERTS (24h):
   Total: {status['recent_alerts']}
   Critical: {status['alert_breakdown']['critical']}
   Warning:  {status['alert_breakdown']['warning']}
   Info:     {status['alert_breakdown']['info']}

📊 BASELINE METRICS:
   Avg Cost/Operation: ${status['baseline_metrics'].get('avg_cost_per_operation', 0):.6f}
   Avg Cost/1K Tokens: ${status['baseline_metrics'].get('avg_cost_per_1k_tokens', 0):.4f}
   Avg Latency: {status['baseline_metrics'].get('avg_latency_ms', 0):.0f}ms

🎯 CONFIGURATION:
   Daily Limit: ${self.config.daily_limit:.2f}
   Hourly Limit: ${self.config.hourly_limit:.2f}
   Spike Threshold: {self.config.spike_threshold}x baseline
   Efficiency Target: ${self.config.efficiency_min:.4f}/1K tokens
   
   Alert Channels:
   - Console: {'✅' if self.config.console_enabled else '❌'}
   - Slack: {'✅' if self.config.slack_enabled else '❌'}
   - Email: {'✅' if self.config.email_enabled else '❌'}

💡 RECOMMENDATIONS:
"""
        
        # Add recommendations based on current status
        if status['daily_usage']['percentage'] > 80:
            report += "   - ⚠️ Daily budget is high - consider optimizing prompts\n"
        
        if status['hourly_usage']['percentage'] > 70:
            report += "   - ⚠️ High hourly usage - monitor upcoming operations\n"
        
        if status['recent_alerts'] > 5:
            report += "   - 🔍 Many recent alerts - review thresholds and operations\n"
        
        if status['recent_alerts'] == 0:
            report += "   - ✅ No recent alerts - system operating within budget\n"
        
        return report


# Integration functions for existing cost_logger.py
def check_budget_integration(pr_url: str, operation: str, cost: float, 
                           latency_ms: int, tokens: int) -> None:
    """
    Integration function to be called from cost_logger.py
    Checks budget limits after each operation
    """
    try:
        # Initialize budget guard (singleton pattern)
        if not hasattr(check_budget_integration, '_guard'):
            check_budget_integration._guard = BudgetGuard()
        
        guard = check_budget_integration._guard
        
        # Check budget limits with current operation context
        alerts = guard.check_budget_limits(pr_url=pr_url, operation=operation)
        
        # Log integration status to current span
        span = get_current_span()
        if span and span.is_recording():
            span.set_attributes({
                "budget.integration.enabled": True,
                "budget.check.alerts_triggered": len(alerts),
                "budget.check.operation": operation
            })
            
            if alerts:
                span.add_event("budget_check_completed", {
                    "alerts_count": len(alerts),
                    "highest_severity": max(alert.severity for alert in alerts) if alerts else "none"
                })
        
    except Exception as e:
        print(f"⚠️ Budget integration error: {e}")
        
        # Log error to span
        span = get_current_span()
        if span and span.is_recording():
            span.set_attributes({
                "budget.integration.error": str(e),
                "budget.integration.enabled": False
            })


# CLI interface for budget guard management
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="🛡️ Secure PR Guard Budget Monitor")
    parser.add_argument('--check', action='store_true', help='Check current budget status')
    parser.add_argument('--report', action='store_true', help='Generate budget report')
    parser.add_argument('--test-alerts', action='store_true', help='Test alert system')
    parser.add_argument('--config', help='Path to config file')
    
    args = parser.parse_args()
    
    # Initialize budget guard
    config_path = args.config or "monitoring/budget_config.yaml"
    guard = BudgetGuard(config_path=config_path)
    
    if args.check:
        print("🔍 Checking budget status...")
        status = guard.get_budget_status()
        print(json.dumps(status, indent=2, default=str))
    
    elif args.report:
        print(guard.generate_budget_report())
    
    elif args.test_alerts:
        print("🧪 Testing alert system...")
        
        # Create test alert
        test_alert = Alert(
            timestamp=datetime.now(),
            alert_type='test_alert',
            severity='warning',
            message='Test alert from Budget Guard system',
            current_value=1.0,
            threshold=0.5,
            pr_url='https://github.com/test/repo/pull/42',
            operation='test_operation'
        )
        
        guard._process_alert(test_alert)
        print("✅ Test alert sent through all configured channels")
    
    else:
        print("🛡️ Budget Guard System Initialized")
        print("Use --check, --report, or --test-alerts options")
        print(f"Configuration: {config_path}")
        print(f"Cost data: {guard.csv_path}")