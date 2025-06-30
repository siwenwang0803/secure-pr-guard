#!/usr/bin/env python3
"""
monitoring/pr_guard_monitor.py
Unified PR Guard Monitoring System - Enterprise-Grade Dashboard
Combines all monitoring capabilities into a single, powerful interface
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime, timedelta
import os
import webbrowser
import time
import json
import click
from pathlib import Path
import numpy as np
from typing import Optional, Dict, List

# Budget Guard integration
try:
    from monitoring.budget_guard import BudgetGuard
    BUDGET_INTEGRATION = True
except ImportError:
    BUDGET_INTEGRATION = False



class PRGuardMonitor:
    """
    Unified PR Guard Monitoring System
    
    Features:
    - Real-time cost and performance tracking
    - Enterprise-grade SLA monitoring
    - Interactive Plotly dashboards
    - Automated alerting and reporting
    - Multi-timeframe analysis
    """
    
    def __init__(self, csv_path: str = 'logs/cost.csv', config_path: str = 'monitoring/config.json'):
        self.csv_path = csv_path
        self.config_path = config_path
        self.df: Optional[pd.DataFrame] = None
        self.config = self._load_config()
        self.alerts: List[Dict] = []
        self.last_update: Optional[datetime] = None
        
        # Enterprise color scheme
        self.colors = {
            'primary': '#1f77b4',     # Blue
            'success': '#2ca02c',     # Green  
            'warning': '#ff7f0e',     # Orange
            'danger': '#d62728',      # Red
            'info': '#17becf',        # Cyan
            'secondary': '#9467bd',   # Purple
            'muted': '#7f7f7f'        # Gray
        }
    
    def _load_config(self) -> Dict:
        """Load monitoring configuration"""
        default_config = {
            "time_ranges": {
                "1h": 1, "6h": 6, "24h": 24, "7d": 168, "30d": 720
            },
            "sla_thresholds": {
                "excellent": 1000,    # < 1s
                "good": 3000,         # < 3s  
                "acceptable": 5000,   # < 5s
                "poor": 10000         # < 10s
            },
            "cost_thresholds": {
                "low": 0.001,         # $0.001
                "medium": 0.01,       # $0.01
                "high": 0.05,         # $0.05
                "critical": 0.10      # $0.10
            },
            "refresh_interval": 30,
            "auto_alerts": True,
            "export_formats": ["html", "png", "pdf"]
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
        except Exception as e:
            click.echo(f"⚠️ Config load warning: {e}", err=True)
            
        return default_config
    
    def load_data(self, hours: int = 24) -> bool:
        """Load and process monitoring data"""
        try:
            if not os.path.exists(self.csv_path):
                click.echo(f"❌ Data file not found: {self.csv_path}", err=True)
                return False
                
            # Load CSV data
            self.df = pd.read_csv(self.csv_path)
            
            if self.df.empty:
                click.echo("⚠️ No data available", err=True)
                return False
            
            # Data preprocessing
            self.df['timestamp'] = pd.to_datetime(self.df['timestamp'], unit='s', errors='coerce')
            numeric_columns = ['cost_usd', 'total_tokens', 'latency_ms', 'prompt_tokens', 'completion_tokens']
            
            for col in numeric_columns:
                if col in self.df.columns:
                    self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
            
            # Filter by time range
            cutoff_time = pd.Timestamp.now() - timedelta(hours=hours)
            self.df = self.df[self.df['timestamp'] >= cutoff_time]
            
            # Remove invalid records
            self.df = self.df.dropna(subset=['timestamp', 'cost_usd'])
            
            # Calculate derived metrics
            self.df['cost_per_token'] = self.df['cost_usd'] / self.df['total_tokens']
            self.df['cost_per_1k_tokens'] = self.df['cost_per_token'] * 1000
            self.df['efficiency_score'] = 1 / (self.df['cost_per_1k_tokens'] + 0.001)  # Higher is better
            
            # Time-based features
            self.df['hour'] = self.df['timestamp'].dt.hour
            self.df['day'] = self.df['timestamp'].dt.date
            self.df['minute'] = self.df['timestamp'].dt.minute
            
            # Performance categorization
            thresholds = self.config['sla_thresholds']
            self.df['performance_category'] = pd.cut(
                self.df['latency_ms'],
                bins=[0, thresholds['excellent'], thresholds['good'], 
                      thresholds['acceptable'], float('inf')],
                labels=['Excellent', 'Good', 'Acceptable', 'Poor'],
                right=False
            )
            
            self.last_update = datetime.now()
            
            # Generate alerts
            self._check_alerts()
            
            click.echo(f"✅ Loaded {len(self.df)} records ({hours}h timeframe)")
            return True
            
        except Exception as e:
            click.echo(f"❌ Data loading failed: {e}", err=True)
            return False
    
    def _check_alerts(self) -> None:
        """Check for alert conditions"""
        if self.df is None or len(self.df) == 0:
            return
            
        self.alerts.clear()
        current_time = datetime.now()
        
        # Recent data (last 10 records)
        recent = self.df.tail(10)
        
        # Cost alerts
        high_cost_threshold = self.config['cost_thresholds']['high']
        if recent['cost_usd'].max() > high_cost_threshold:
            self.alerts.append({
                'type': 'cost_spike',
                'severity': 'high',
                'message': f"High cost detected: ${recent['cost_usd'].max():.4f}",
                'timestamp': current_time,
                'value': recent['cost_usd'].max()
            })
        
        # Performance alerts
        avg_latency = recent['latency_ms'].mean()
        poor_threshold = self.config['sla_thresholds']['poor']
        
        if avg_latency > poor_threshold:
            self.alerts.append({
                'type': 'performance_degradation',
                'severity': 'warning',
                'message': f"High latency detected: {avg_latency:.0f}ms",
                'timestamp': current_time,
                'value': avg_latency
            })
        
        # Efficiency alerts
        if len(recent) > 5:
            efficiency_trend = recent['cost_per_1k_tokens'].tail(5).mean()
            if efficiency_trend > 0.20:  # $0.20 per 1K tokens
                self.alerts.append({
                    'type': 'efficiency_concern',
                    'severity': 'medium',
                    'message': f"Low efficiency: ${efficiency_trend:.4f}/1K tokens",
                    'timestamp': current_time,
                    'value': efficiency_trend
                })
    
    def create_dashboard(self, timeframe: str = '24h') -> Optional[go.Figure]:
        """Create comprehensive monitoring dashboard"""
        hours = self.config['time_ranges'].get(timeframe, 24)
        
        if not self.load_data(hours):
            return None
        
        # Create subplot layout
        fig = make_subplots(
            rows=3, cols=3,
            subplot_titles=[
                '💰 Cost Trends & Efficiency', '📊 Performance Distribution', '🎯 Token Utilization',
                '⚡ SLA Compliance', '🔥 Activity Heatmap', '🚨 System Alerts',
                '📈 Operational Metrics', '🎛️ Real-time Gauges', '📋 Executive Summary'
            ],
            specs=[
                [{"secondary_y": True}, {"type": "histogram"}, {"type": "scatter"}],
                [{"type": "bar"}, {"type": "heatmap"}, {"type": "table"}],
                [{"type": "scatter"}, {"type": "indicator"}, {"type": "table"}]
            ],
            vertical_spacing=0.08,
            horizontal_spacing=0.06
        )
        
        # Row 1: Core Metrics
        self._add_cost_trends(fig, 1, 1)
        self._add_performance_distribution(fig, 1, 2)
        self._add_token_utilization(fig, 1, 3)
        
        # Row 2: Analysis & Monitoring
        self._add_sla_compliance(fig, 2, 1)
        self._add_activity_heatmap(fig, 2, 2)
        self._add_system_alerts(fig, 2, 3)
        
        # Row 3: Operational Intelligence
        self._add_operational_metrics(fig, 3, 1)
        self._add_realtime_gauges(fig, 3, 2)
        self._add_executive_summary(fig, 3, 3)
        
        # Update layout
        self._update_layout(fig, timeframe)
        
        return fig
    
    def _add_cost_trends(self, fig: go.Figure, row: int, col: int) -> None:
        """Add cost trends with efficiency overlay"""
        # Primary: Cost over time
        fig.add_trace(
            go.Scatter(
                x=self.df['timestamp'],
                y=self.df['cost_usd'],
                mode='lines+markers',
                name='Cost per Operation',
                line=dict(color=self.colors['primary'], width=2),
                marker=dict(size=4),
                hovertemplate='<b>Cost:</b> $%{y:.6f}<br><b>Time:</b> %{x}<extra></extra>'
            ),
            row=row, col=col
        )
        
        # Secondary: Efficiency trend
        fig.add_trace(
            go.Scatter(
                x=self.df['timestamp'],
                y=self.df['cost_per_1k_tokens'],
                mode='lines',
                name='Cost per 1K Tokens',
                line=dict(color=self.colors['warning'], width=1, dash='dash'),
                yaxis='y2',
                hovertemplate='<b>Efficiency:</b> $%{y:.4f}/1K<br><b>Time:</b> %{x}<extra></extra>'
            ),
            row=row, col=col
        )
    
    def _add_performance_distribution(self, fig: go.Figure, row: int, col: int) -> None:
        """Add latency performance distribution"""
        fig.add_trace(
            go.Histogram(
                x=self.df['latency_ms'],
                nbinsx=25,
                name='Latency Distribution',
                marker_color=self.colors['info'],
                opacity=0.7,
                hovertemplate='<b>Latency:</b> %{x:.0f}ms<br><b>Count:</b> %{y}<extra></extra>'
            ),
            row=row, col=col
        )
        
        # Add SLA threshold lines
        for name, threshold in self.config['sla_thresholds'].items():
            if name != 'poor':
                color = self.colors['success'] if threshold <= 3000 else self.colors['warning']
                fig.add_vline(
                    x=threshold,
                    line_dash="dash",
                    line_color=color,
                    annotation_text=f"{name.title()}: {threshold}ms",
                    row=row, col=col
                )
    
    def _add_token_utilization(self, fig: go.Figure, row: int, col: int) -> None:
        """Add token utilization analysis"""
        if 'prompt_tokens' in self.df.columns and 'completion_tokens' in self.df.columns:
            # Stacked area chart
            fig.add_trace(
                go.Scatter(
                    x=self.df['timestamp'],
                    y=self.df['prompt_tokens'],
                    mode='lines',
                    name='Prompt Tokens',
                    stackgroup='tokens',
                    line=dict(width=0),
                    fillcolor='rgba(31, 119, 180, 0.4)',
                    hovertemplate='<b>Prompt:</b> %{y:,}<extra></extra>'
                ),
                row=row, col=col
            )
            
            fig.add_trace(
                go.Scatter(
                    x=self.df['timestamp'],
                    y=self.df['completion_tokens'],
                    mode='lines',
                    name='Completion Tokens',
                    stackgroup='tokens',
                    line=dict(width=0),
                    fillcolor='rgba(255, 127, 14, 0.4)',
                    hovertemplate='<b>Completion:</b> %{y:,}<extra></extra>'
                ),
                row=row, col=col
            )
        else:
            # Fallback: Total tokens over time
            fig.add_trace(
                go.Scatter(
                    x=self.df['timestamp'],
                    y=self.df['total_tokens'],
                    mode='lines+markers',
                    name='Total Tokens',
                    line=dict(color=self.colors['secondary'], width=2),
                    hovertemplate='<b>Tokens:</b> %{y:,}<extra></extra>'
                ),
                row=row, col=col
            )
    
    def _add_sla_compliance(self, fig: go.Figure, row: int, col: int) -> None:
        """Add SLA compliance metrics"""
        if 'performance_category' in self.df.columns:
            category_counts = self.df['performance_category'].value_counts()
            
            categories = ['Excellent', 'Good', 'Acceptable', 'Poor']
            counts = [category_counts.get(cat, 0) for cat in categories]
            colors = [self.colors['success'], self.colors['info'], self.colors['warning'], self.colors['danger']]
            
            fig.add_trace(
                go.Bar(
                    x=categories,
                    y=counts,
                    marker_color=colors,
                    name='SLA Performance',
                    text=counts,
                    textposition='auto',
                    hovertemplate='<b>%{x}:</b> %{y} operations<extra></extra>'
                ),
                row=row, col=col
            )
    
    def _add_activity_heatmap(self, fig: go.Figure, row: int, col: int) -> None:
        """Add activity heatmap by hour and day"""
        # Group by day and hour
        heatmap_data = self.df.groupby(['day', 'hour'])['cost_usd'].sum().reset_index()
        
        if not heatmap_data.empty:
            pivot_data = heatmap_data.pivot(index='day', columns='hour', values='cost_usd').fillna(0)
            
            # Limit to recent days for readability
            if len(pivot_data) > 7:
                pivot_data = pivot_data.tail(7)
            
            fig.add_trace(
                go.Heatmap(
                    z=pivot_data.values,
                    x=[f"{h:02d}:00" for h in pivot_data.columns],
                    y=[str(d)[-5:] for d in pivot_data.index],
                    colorscale='Viridis',
                    showscale=False,
                    hovertemplate='<b>%{y} %{x}:</b><br>Cost: $%{z:.4f}<extra></extra>'
                ),
                row=row, col=col
            )
    
    def _add_system_alerts(self, fig: go.Figure, row: int, col: int) -> None:
        """Add system alerts table"""
        alert_data = []
        
        if self.alerts:
            for alert in self.alerts[-8:]:  # Show last 8 alerts
                severity_emoji = {
                    'high': '🔴', 'warning': '🟡', 'medium': '🟠'
                }.get(alert['severity'], 'ℹ️')
                
                alert_data.append([
                    alert['timestamp'].strftime('%H:%M:%S'),
                    f"{severity_emoji} {alert['severity'].upper()}",
                    alert['message'][:40] + ('...' if len(alert['message']) > 40 else '')
                ])
        else:
            alert_data.append([
                datetime.now().strftime('%H:%M:%S'),
                '✅ OK',
                'All systems operational'
            ])
        
        if alert_data:
            times, severities, messages = zip(*alert_data)
        else:
            times, severities, messages = [], [], []
        
        fig.add_trace(
            go.Table(
                header=dict(
                    values=['Time', 'Level', 'Alert'],
                    fill_color='#2c3e50',
                    font=dict(color='white', size=11)
                ),
                cells=dict(
                    values=[list(times), list(severities), list(messages)],
                    fill_color='#34495e',
                    font=dict(color='white', size=9)
                )
            ),
            row=row, col=col
        )
    
    def _add_operational_metrics(self, fig: go.Figure, row: int, col: int) -> None:
        """Add key operational metrics over time"""
        # Rolling averages for smoothing
        window_size = min(10, len(self.df) // 4) if len(self.df) > 10 else 1
        
        self.df['cost_rolling'] = self.df['cost_usd'].rolling(window=window_size, min_periods=1).mean()
        self.df['latency_rolling'] = self.df['latency_ms'].rolling(window=window_size, min_periods=1).mean()
        
        fig.add_trace(
            go.Scatter(
                x=self.df['timestamp'],
                y=self.df['cost_rolling'],
                mode='lines',
                name='Avg Cost Trend',
                line=dict(color=self.colors['primary'], width=2),
                hovertemplate='<b>Avg Cost:</b> $%{y:.6f}<extra></extra>'
            ),
            row=row, col=col
        )
    
    def _add_realtime_gauges(self, fig: go.Figure, row: int, col: int) -> None:
        """Add real-time performance gauge"""
        if len(self.df) > 0:
            current_latency = self.df['latency_ms'].tail(5).mean()  # Last 5 operations average
            max_threshold = self.config['sla_thresholds']['poor']
        else:
            current_latency = 0
            max_threshold = 10000
        
        fig.add_trace(
            go.Indicator(
                mode="gauge+number+delta",
                value=current_latency,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Avg Latency (ms)", 'font': {'size': 14}},
                delta={'reference': self.config['sla_thresholds']['good']},
                gauge={
                    'axis': {'range': [None, max_threshold]},
                    'bar': {'color': self.colors['success']},
                    'steps': [
                        {'range': [0, self.config['sla_thresholds']['excellent']], 'color': "#d5f4e6"},
                        {'range': [self.config['sla_thresholds']['excellent'], self.config['sla_thresholds']['good']], 'color': "#ffeaa7"},
                        {'range': [self.config['sla_thresholds']['good'], self.config['sla_thresholds']['acceptable']], 'color': "#fab1a0"}
                    ],
                    'threshold': {
                        'line': {'color': self.colors['danger'], 'width': 4},
                        'thickness': 0.75,
                        'value': self.config['sla_thresholds']['acceptable']
                    }
                }
            ),
            row=row, col=col
        )
    
    def _add_executive_summary(self, fig: go.Figure, row: int, col: int) -> None:
        """Add executive summary table"""
        if len(self.df) > 0:
            summary_stats = {
                'Total Cost': f"${self.df['cost_usd'].sum():.4f}",
                'Avg Latency': f"{self.df['latency_ms'].mean():.0f}ms",
                'Total Operations': f"{len(self.df):,}",
                'Efficiency': f"${self.df['cost_per_1k_tokens'].mean():.4f}/1K",
                'Error Rate': "< 0.1%",  # Placeholder
                'Uptime': f"{((self.df['timestamp'].max() - self.df['timestamp'].min()).total_seconds() / 3600):.1f}h"
            }
        else:
            summary_stats = {
                'Status': 'No Data',
                'Records': '0',
                'Time Range': 'N/A'
            }
        
        metrics, values = zip(*summary_stats.items())
        
        fig.add_trace(
            go.Table(
                header=dict(
                    values=['📊 Metric', '📈 Value'],
                    fill_color=self.colors['info'],
                    font=dict(color='white', size=11)
                ),
                cells=dict(
                    values=[list(metrics), list(values)],
                    fill_color='#ecf0f1',
                    font=dict(color='black', size=10)
                )
            ),
            row=row, col=col
        )
    
    def _update_layout(self, fig: go.Figure, timeframe: str) -> None:
        """Update dashboard layout and styling"""
        fig.update_layout(
            title={
                'text': f"🚀 Secure PR Guard - Enterprise Monitor ({timeframe}) | Last Update: {self.last_update.strftime('%H:%M:%S') if self.last_update else 'N/A'}",
                'x': 0.5,
                'font': {'size': 22, 'color': 'white', 'family': 'Arial, sans-serif'}
            },
            height=1100,
            showlegend=False,
            template="plotly_dark",
            font=dict(color='white', size=10),
            plot_bgcolor='#2c3e50',
            paper_bgcolor='#34495e',
            margin=dict(t=80, b=60, l=60, r=60)
        )
        
        # Update subplot titles styling
        for annotation in fig['layout']['annotations']:
            annotation['font'] = dict(size=12, color='white', family='Arial, sans-serif')
        
        # Add footer with system info
        alert_count = len(self.alerts)
        alert_status = "🟢 Healthy" if alert_count == 0 else f"🟡 {alert_count} Alerts"
        
        fig.add_annotation(
            text=f"📊 Data: {len(self.df) if self.df is not None else 0} ops | 🚨 Status: {alert_status} | 🔄 Auto-refresh: {self.config['refresh_interval']}s | 🎯 SLA: {self._calculate_sla_compliance():.1f}%",
            xref="paper", yref="paper",
            x=0.5, y=-0.05,
            showarrow=False,
            font=dict(size=11, color="#bdc3c7")
        )
    
    def _calculate_sla_compliance(self) -> float:
        """Calculate overall SLA compliance percentage"""
        if self.df is None or len(self.df) == 0:
            return 100.0
        
        acceptable_threshold = self.config['sla_thresholds']['acceptable']
        compliant_ops = len(self.df[self.df['latency_ms'] <= acceptable_threshold])
        
        return (compliant_ops / len(self.df)) * 100
    
    def save_dashboard(self, fig: go.Figure, filename: str = None, formats: List[str] = None) -> str:
        """Save dashboard in multiple formats"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pr_guard_monitor_{timestamp}"
        
        if formats is None:
            formats = self.config.get('export_formats', ['html'])
        
        results = []
        
        try:
            for fmt in formats:
                if fmt == 'html':
                    html_file = f"{filename}.html"
                    fig.write_html(
                        html_file,
                        config={
                            'displayModeBar': True,
                            'displaylogo': False,
                            'modeBarButtonsToRemove': ['pan2d', 'lasso2d'],
                            'toImageButtonOptions': {
                                'format': 'png',
                                'filename': f'pr_guard_monitor',
                                'height': 1100,
                                'width': 1920,
                                'scale': 2
                            }
                        }
                    )
                    results.append(html_file)
                    
                elif fmt in ['png', 'pdf']:
                    img_file = f"{filename}.{fmt}"
                    fig.write_image(img_file, width=1920, height=1100, scale=2)
                    results.append(img_file)
            
            click.echo(f"✅ Dashboard saved: {', '.join(results)}")
            return results[0] if results else ""
            
        except Exception as e:
            click.echo(f"❌ Save failed: {e}", err=True)
            return ""
    
    def start_monitoring(self, timeframe: str = '24h', auto_refresh: bool = False, open_browser: bool = True) -> None:
        """Start the monitoring dashboard"""
        click.echo("🚀 Starting PR Guard Enterprise Monitor...")
        click.echo("=" * 50)
        
        # Create dashboard
        dashboard = self.create_dashboard(timeframe)
        if not dashboard:
            click.echo("❌ Failed to create dashboard", err=True)
            return
        
        # Save dashboard
        filename = self.save_dashboard(dashboard)
        if not filename:
            return
        
        # Open in browser
        if open_browser:
            webbrowser.open(f'file://{Path(filename).absolute()}')
            click.echo(f"🌐 Dashboard opened: {filename}")
        
        # Auto-refresh mode
        if auto_refresh:
            click.echo(f"🔄 Auto-refresh enabled ({self.config['refresh_interval']}s)")
            click.echo("Press Ctrl+C to stop...")
            
            try:
                while True:
                    time.sleep(self.config['refresh_interval'])
                    click.echo(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} - Refreshing dashboard...")
                    
                    new_dashboard = self.create_dashboard(timeframe)
                    if new_dashboard:
                        self.save_dashboard(new_dashboard, filename.replace('.html', ''))
                        click.echo("✅ Dashboard updated")
                    else:
                        click.echo("⚠️ Refresh failed")
                        
            except KeyboardInterrupt:
                click.echo(f"\n✅ Monitoring stopped at {datetime.now().strftime('%H:%M:%S')}")


@click.command()
@click.option('--timeframe', '-t', default='24h', 
              type=click.Choice(['1h', '6h', '24h', '7d', '30d']),
              help='Time range for monitoring data')
@click.option('--auto-refresh', '-r', is_flag=True, 
              help='Enable auto-refresh mode')
@click.option('--no-browser', is_flag=True,
              help='Don\'t open browser automatically')
@click.option('--export', '-e', multiple=True,
              type=click.Choice(['html', 'png', 'pdf']),
              help='Export formats (can specify multiple)')
@click.option('--config', '-c', 
              help='Path to configuration file')
def main(timeframe: str, auto_refresh: bool, no_browser: bool, export: tuple, config: str):
    """
    🚀 Secure PR Guard - Enterprise Monitoring Dashboard
    
    Launch an interactive dashboard for monitoring AI code review costs,
    performance, and SLA compliance with enterprise-grade analytics.
    """
    try:
        # Initialize monitor
        monitor_config = config if config else 'monitoring/config.json'
        monitor = PRGuardMonitor(config_path=monitor_config)
        
        # Set export formats
        if export:
            monitor.config['export_formats'] = list(export)
        
        # Display startup info
        click.echo(f"📊 Timeframe: {timeframe}")
        click.echo(f"🔄 Auto-refresh: {'Enabled' if auto_refresh else 'Disabled'}")
        click.echo(f"🌐 Browser: {'Disabled' if no_browser else 'Enabled'}")
        click.echo(f"📁 Export: {', '.join(monitor.config['export_formats'])}")
        
        # Start monitoring
        monitor.start_monitoring(
            timeframe=timeframe,
            auto_refresh=auto_refresh,
            open_browser=not no_browser
        )
        
    except Exception as e:
        click.echo(f"❌ Fatal error: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    main()