#!/usr/bin/env python3
"""
monitoring/fixed_monitor.py
Fixed Enterprise Dashboard - All Syntax Errors Resolved
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
from pathlib import Path
import numpy as np


class FixedEnterpriseDashboard:
    """Fixed Enterprise-Grade Dashboard"""
    
    def __init__(self, csv_path='logs/cost.csv'):
        self.csv_path = csv_path
        self.df = None
        self.last_update = None
        self.data_quality_issues = []
        
        # Fixed color scheme
        self.colors = {
            'critical': '#FF4C4C',
            'warning': '#FDB750', 
            'normal': '#4CAF50',
            'info': '#2196F3',
            'cost': '#9C27B0',
            'latency': '#FF5722',
            'tokens': '#607D8B'
        }
        
        self.config = {
            "sla_thresholds": {
                "fast": 1000,
                "normal": 5000,
                "slow": 10000,
                "critical": 15000
            },
            "alert_thresholds": {
                "latency_p95": 8000,
                "latency_p99": 12000
            }
        }
    
    def load_data(self, time_range_hours=24) -> bool:
        """Load and validate data"""
        try:
            if not os.path.exists(self.csv_path):
                print(f"❌ CSV file not found: {self.csv_path}")
                return False
                
            self.df = pd.read_csv(self.csv_path)
            
            if self.df.empty:
                print("⚠️ CSV file is empty")
                return False
            
            # Data conversion
            self.df['timestamp'] = pd.to_datetime(self.df['timestamp'], unit='s', errors='coerce')
            self.df['cost_usd'] = pd.to_numeric(self.df['cost_usd'], errors='coerce')
            self.df['total_tokens'] = pd.to_numeric(self.df['total_tokens'], errors='coerce')
            self.df['latency_ms'] = pd.to_numeric(self.df['latency_ms'], errors='coerce')
            
            # Filter by time range
            cutoff_time = pd.Timestamp.now() - timedelta(hours=time_range_hours)
            self.df = self.df[self.df['timestamp'] >= cutoff_time]
            
            # Remove invalid data
            self.df = self.df.dropna(subset=['timestamp', 'cost_usd'])
            
            # Add calculated fields
            self.df['cost_per_1k_tokens'] = (self.df['cost_usd'] / self.df['total_tokens'] * 1000).fillna(0)
            self.df['hour'] = self.df['timestamp'].dt.hour
            self.df['date'] = self.df['timestamp'].dt.date
            
            self.df = self.df.sort_values('timestamp')
            self.last_update = datetime.now()
            
            print(f"✅ Loaded {len(self.df)} records")
            return True
            
        except Exception as e:
            print(f"❌ Data loading error: {e}")
            return False
    
    def calculate_sla_metrics(self) -> dict:
        """Calculate SLA metrics"""
        if self.df is None or self.df.empty:
            return {
                'p50': 0, 'p95': 0, 'p99': 0, 'avg': 0, 'max': 0,
                'fast_count': 0, 'normal_count': 0, 'slow_count': 0, 'critical_count': 0
            }
        
        latency_data = self.df['latency_ms'].dropna()
        
        return {
            'p50': latency_data.quantile(0.50),
            'p95': latency_data.quantile(0.95), 
            'p99': latency_data.quantile(0.99),
            'avg': latency_data.mean(),
            'max': latency_data.max(),
            'fast_count': len(self.df[self.df['latency_ms'] < self.config['sla_thresholds']['fast']]),
            'normal_count': len(self.df[
                (self.df['latency_ms'] >= self.config['sla_thresholds']['fast']) & 
                (self.df['latency_ms'] < self.config['sla_thresholds']['normal'])
            ]),
            'slow_count': len(self.df[
                (self.df['latency_ms'] >= self.config['sla_thresholds']['normal']) & 
                (self.df['latency_ms'] < self.config['sla_thresholds']['critical'])
            ]),
            'critical_count': len(self.df[self.df['latency_ms'] >= self.config['sla_thresholds']['critical']])
        }
    
    def create_dashboard(self, time_range_hours=24) -> go.Figure:
        """Create fixed dashboard"""
        if not self.load_data(time_range_hours):
            return None
        
        sla_metrics = self.calculate_sla_metrics()
        
        # Create 3x3 layout for better fit
        fig = make_subplots(
            rows=3, cols=3,
            subplot_titles=(
                '💰 Cost Trends', '🎯 Token Usage', '⚡ Latency Distribution',
                '📊 SLA Performance', '🔥 Cost Heatmap', '🚨 System Health',
                '📈 Percentiles', '🎛️ Live Latency', '📋 Summary'
            ),
            specs=[
                [{"type": "scatter"}, {"type": "scatter"}, {"type": "histogram"}],
                [{"type": "bar"}, {"type": "heatmap"}, {"type": "table"}],
                [{"type": "bar"}, {"type": "indicator"}, {"type": "table"}]
            ],
            vertical_spacing=0.1,
            horizontal_spacing=0.08
        )
        
        # Add all charts
        self.add_cost_trends(fig, 1, 1)
        self.add_token_usage(fig, 1, 2)
        self.add_latency_distribution(fig, 1, 3)
        self.add_sla_performance(fig, 2, 1, sla_metrics)
        self.add_cost_heatmap(fig, 2, 2)
        self.add_system_health(fig, 2, 3)
        self.add_percentiles_chart(fig, 3, 1, sla_metrics)
        self.add_latency_gauge(fig, 3, 2, sla_metrics)
        self.add_summary_table(fig, 3, 3)
        
        # Update layout
        fig.update_layout(
            title={
                'text': f"🚀 Secure PR Guard - Enterprise Monitor ({time_range_hours}h)",
                'x': 0.5,
                'font': {'size': 20, 'color': 'white'}
            },
            height=1000,
            showlegend=False,
            template="plotly_dark",
            font=dict(color='white', size=10),
            plot_bgcolor='#1a1a1a',
            paper_bgcolor='#0d1117',
            margin=dict(t=70, b=50, l=50, r=50)
        )
        
        return fig
    
    def add_cost_trends(self, fig, row, col):
        """Cost trends chart"""
        fig.add_trace(
            go.Scatter(
                x=self.df['timestamp'],
                y=self.df['cost_usd'],
                mode='lines+markers',
                name='Cost',
                line=dict(color=self.colors['cost'], width=2),
                marker=dict(size=4),
                hovertemplate='<b>Cost:</b> $%{y:.6f}<br><b>Time:</b> %{x}<extra></extra>'
            ),
            row=row, col=col
        )
    
    def add_token_usage(self, fig, row, col):
        """Token usage with fixed colors"""
        # Get token columns or create zeros
        prompt_tokens = self.df.get('prompt_tokens', pd.Series([0] * len(self.df)))
        completion_tokens = self.df.get('completion_tokens', pd.Series([0] * len(self.df)))
        
        # Fixed color format
        fig.add_trace(
            go.Scatter(
                x=self.df['timestamp'],
                y=prompt_tokens,
                mode='lines',
                name='Prompt Tokens',
                stackgroup='tokens',
                line=dict(width=0),
                fillcolor='rgba(96, 125, 139, 0.4)',  # Fixed format
                hovertemplate='<b>Prompt:</b> %{y:,}<extra></extra>'
            ),
            row=row, col=col
        )
        
        fig.add_trace(
            go.Scatter(
                x=self.df['timestamp'],
                y=completion_tokens,
                mode='lines',
                name='Completion Tokens',
                stackgroup='tokens',
                line=dict(width=0),
                fillcolor='rgba(33, 150, 243, 0.4)',  # Fixed format
                hovertemplate='<b>Completion:</b> %{y:,}<extra></extra>'
            ),
            row=row, col=col
        )
    
    def add_latency_distribution(self, fig, row, col):
        """Latency distribution"""
        fig.add_trace(
            go.Histogram(
                x=self.df['latency_ms'],
                nbinsx=20,
                name='Latency Distribution',
                marker_color=self.colors['latency'],
                opacity=0.7,
                hovertemplate='<b>Latency:</b> %{x:.0f}ms<br><b>Count:</b> %{y}<extra></extra>'
            ),
            row=row, col=col
        )
    
    def add_sla_performance(self, fig, row, col, sla_metrics):
        """SLA performance bars"""
        categories = ['Fast\n(<1s)', 'Normal\n(1-5s)', 'Slow\n(5-10s)', 'Critical\n(>10s)']
        counts = [
            sla_metrics['fast_count'],
            sla_metrics['normal_count'], 
            sla_metrics['slow_count'],
            sla_metrics['critical_count']
        ]
        colors = [self.colors['normal'], self.colors['info'], self.colors['warning'], self.colors['critical']]
        
        fig.add_trace(
            go.Bar(
                x=categories,
                y=counts,
                marker_color=colors,
                name='SLA Distribution',
                text=counts,
                textposition='auto',
                hovertemplate='<b>Category:</b> %{x}<br><b>Count:</b> %{y}<extra></extra>'
            ),
            row=row, col=col
        )
    
    def add_cost_heatmap(self, fig, row, col):
        """Cost heatmap"""
        heatmap_data = self.df.groupby(['date', 'hour'])['cost_usd'].sum().reset_index()
        
        if not heatmap_data.empty:
            pivot_data = heatmap_data.pivot(index='date', columns='hour', values='cost_usd').fillna(0)
            
            # Limit rows to prevent overlap
            if len(pivot_data) > 5:
                pivot_data = pivot_data.tail(5)
            
            fig.add_trace(
                go.Heatmap(
                    z=pivot_data.values,
                    x=[f"{h:02d}h" for h in pivot_data.columns],
                    y=[str(d)[-5:] for d in pivot_data.index],
                    colorscale='Viridis',
                    showscale=False,
                    hovertemplate='<b>Date:</b> %{y}<br><b>Hour:</b> %{x}<br><b>Cost:</b> $%{z:.4f}<extra></extra>'
                ),
                row=row, col=col
            )
    
    def add_system_health(self, fig, row, col):
        """System health table"""
        health_data = [
            [datetime.now().strftime('%H:%M:%S'), 'OK', '✅ System Healthy'],
            [datetime.now().strftime('%H:%M:%S'), 'INFO', f'📊 {len(self.df)} Records'],
        ]
        
        if self.data_quality_issues:
            for issue in self.data_quality_issues[-3:]:
                health_data.append([
                    datetime.now().strftime('%H:%M:%S'),
                    'WARN',
                    issue[:30] + '...' if len(issue) > 30 else issue
                ])
        
        times, levels, messages = zip(*health_data)
        
        fig.add_trace(
            go.Table(
                header=dict(
                    values=['Time', 'Level', 'Status'],
                    fill_color='#1a1a1a',
                    font=dict(color='white', size=11)
                ),
                cells=dict(
                    values=[list(times), list(levels), list(messages)],
                    fill_color='#2a2a2a',
                    font=dict(color='white', size=9)
                )
            ),
            row=row, col=col
        )
    
    def add_percentiles_chart(self, fig, row, col, sla_metrics):
        """Latency percentiles"""
        percentiles = ['P50', 'P95', 'P99', 'Max']
        values = [
            sla_metrics['p50'],
            sla_metrics['p95'],
            sla_metrics['p99'],
            sla_metrics['max']
        ]
        colors = [self.colors['normal'], self.colors['info'], self.colors['warning'], self.colors['critical']]
        
        fig.add_trace(
            go.Bar(
                x=percentiles,
                y=values,
                marker_color=colors,
                name='Latency Percentiles',
                text=[f"{v:.0f}ms" for v in values],
                textposition='auto',
                hovertemplate='<b>Percentile:</b> %{x}<br><b>Latency:</b> %{y:.0f}ms<extra></extra>'
            ),
            row=row, col=col
        )
    
    def add_latency_gauge(self, fig, row, col, sla_metrics):
        """Fixed latency gauge"""
        current_latency = sla_metrics['avg']
        
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=current_latency,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Avg Latency (ms)", 'font': {'size': 14}},
                gauge={
                    'axis': {'range': [None, 10000]},
                    'bar': {'color': self.colors['normal']},
                    'steps': [
                        {'range': [0, 1000], 'color': "lightgreen"},
                        {'range': [1000, 5000], 'color': "yellow"},
                        {'range': [5000, 10000], 'color': "orange"}
                    ],
                    'threshold': {
                        'line': {'color': self.colors['critical'], 'width': 4},
                        'thickness': 0.75,
                        'value': 8000
                    }
                },
                number={'font': {'size': 16}}
            ),
            row=row, col=col
        )
    
    def add_summary_table(self, fig, row, col):
        """Summary statistics table"""
        if len(self.df) > 0:
            total_cost = self.df['cost_usd'].sum()
            avg_latency = self.df['latency_ms'].mean()
            total_tokens = self.df['total_tokens'].sum()
        else:
            total_cost = avg_latency = total_tokens = 0
        
        summary_data = [
            ['Total Cost', f"${total_cost:.4f}"],
            ['Avg Latency', f"{avg_latency:.0f}ms"],
            ['Total Tokens', f"{total_tokens:,}"],
            ['Records', f"{len(self.df):,}"],
            ['Data Source', 'CSV']
        ]
        
        metrics, values = zip(*summary_data)
        
        fig.add_trace(
            go.Table(
                header=dict(
                    values=['Metric', 'Value'],
                    fill_color=self.colors['info'],
                    font=dict(color='white', size=11)
                ),
                cells=dict(
                    values=[list(metrics), list(values)],
                    fill_color='#2a2a2a',
                    font=dict(color='white', size=10)
                )
            ),
            row=row, col=col
        )
    
    def save_dashboard(self, fig, filename='fixed_enterprise_monitor.html'):
        """Save dashboard"""
        try:
            fig.write_html(filename, config={'displayModeBar': True, 'displaylogo': False})
            print(f"✅ Dashboard saved: {filename}")
            return filename
        except Exception as e:
            print(f"❌ Save failed: {e}")
            return None
    
    def start_monitoring(self):
        """Start monitoring"""
        print("🚀 Fixed Enterprise Monitor")
        print("=" * 30)
        
        try:
            time_range = input("Time range (24h/7d) [24h]: ").lower() or "24h"
            hours = 24 if time_range == "24h" else 168
            
            dashboard = self.create_dashboard(hours)
            if not dashboard:
                print("❌ Cannot create dashboard")
                return
            
            filename = self.save_dashboard(dashboard)
            if filename:
                webbrowser.open(f'file://{Path(filename).absolute()}')
                print("✅ Dashboard opened in browser")
                
        except KeyboardInterrupt:
            print("\n👋 Cancelled")


def main():
    """Main function"""
    monitor = FixedEnterpriseDashboard()
    monitor.start_monitoring()


if __name__ == "__main__":
    main()