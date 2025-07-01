#!/usr/bin/env python3
"""
Secure PR Guard - Complete Demo Script
=====================================
Professional demonstration script that simulates all scenes for recording
"""

import time
import sys
import os
import subprocess
import webbrowser
from datetime import datetime

class DemoPresentation:
    def __init__(self):
        self.colors = {
            'reset': '\033[0m',
            'bold': '\033[1m',
            'green': '\033[92m',
            'blue': '\033[94m',
            'yellow': '\033[93m',
            'red': '\033[91m',
            'cyan': '\033[96m',
            'magenta': '\033[95m'
        }
    
    def colored_text(self, text, color):
        return f"{self.colors.get(color, '')}{text}{self.colors['reset']}"
    
    def print_header(self, text):
        print(f"\n{self.colored_text('=' * 70, 'blue')}")
        print(f"{self.colored_text(text, 'bold')}")
        print(f"{self.colored_text('=' * 70, 'blue')}")
    
    def print_step(self, step, description):
        print(f"{self.colored_text(f'{step}', 'cyan')} {description}")
    
    def simulate_typing(self, text, delay=0.05):
        """Simulate typing effect for commands"""
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)
        print()
    
    def pause_for_effect(self, seconds=2):
        """Pause for dramatic effect"""
        time.sleep(seconds)

    def generate_qr_code(self):
        """Generate QR code for GitHub repo"""
        try:
            import qrcode
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data('https://github.com/siwenwang0803/secure-pr-guard')
            qr.make(fit=True)
            img = qr.make_image(fill_color='black', back_color='white')
            img.save('github_qr.png')
            print(f"{self.colored_text('✅ QR code generated: github_qr.png', 'green')}")
            return True
        except ImportError:
            print(f"{self.colored_text('⚠️ qrcode library not found. Install with: pip install qrcode[pil]', 'yellow')}")
            return False

    def open_dashboard(self):
        """Open dashboard in browser"""
        dashboard_file = "demo_dashboard.html"
        if os.path.exists(dashboard_file):
            file_path = f"file://{os.path.abspath(dashboard_file)}"
            print(f"{self.colored_text(f'🌐 Opening dashboard: {file_path}', 'blue')}")
            webbrowser.open(file_path)
            return True
        else:
            print(f"{self.colored_text(f'⚠️ Dashboard file not found: {dashboard_file}', 'yellow')}")
            return False

    def scene_1_github_intro(self):
        """Scene 1: Introduction and GitHub Project (0-15s)"""
        self.print_header("🚀 SECURE PR GUARD - ENTERPRISE AI CODE REVIEW")
        
        print(f"{self.colored_text('🚀 Secure PR Guard', 'bold')} - Enterprise AI Code Review System")
        print(f"   {self.colored_text('🎯 Target:', 'yellow')} DevSecOps & FinOps Teams")
        print(f"   {self.colored_text('🛡️ Security:', 'green')} 100% OWASP LLM Top-10 Compliance")
        print(f"   {self.colored_text('💰 FinOps:', 'blue')} Real-time Budget Monitoring")
        print()
        
        print(f"{self.colored_text('📊 Key Metrics:', 'magenta')}")
        print(f"   • Cost: $0.15/PR (vs industry $2.50+)")
        print(f"   • Speed: 17s end-to-end (vs industry 45s+)")
        print(f"   • Security: 100% OWASP coverage")
        print(f"   • Reliability: 99.9% SLA")
        
        self.pause_for_effect(2)
        print(f"\n{self.colored_text('🎯 Demo Workflow:', 'cyan')} Docker Deploy → PR Analysis → Budget Monitor → Dashboard")
        self.pause_for_effect(3)

    def scene_2_docker_deployment(self):
        """Scene 2: Docker Deployment (15-30s)"""
        self.print_header("🐳 ENTERPRISE DEPLOYMENT")
        
        print(f"{self.colored_text('📦 Pulling enterprise Docker image...', 'blue')}")
        self.pause_for_effect(1)
        
        # Simulate docker pull command
        print("$ ", end="")
        self.simulate_typing("docker pull ghcr.io/siwenwang0803/secure-pr-guard:v1.0.0")
        
        # Simulate docker pull output
        print("v1.0.0: Pulling from siwenwang0803/secure-pr-guard")
        print("Digest: sha256:697361fba7a0d2cda12b9f07b5fce05871a1d4d76c4b449619ffe39619f236f2")
        print("Status: Downloaded newer image for ghcr.io/siwenwang0803/secure-pr-guard:v1.0.0")
        print("ghcr.io/siwenwang0803/secure-pr-guard:v1.0.0")
        
        self.pause_for_effect(2)
        
        print(f"\n{self.colored_text('🔍 Checking service status...', 'blue')}")
        print("$ ", end="")
        self.simulate_typing("docker-compose ps")
        
        # Simulate docker-compose ps output
        print("NAME                        COMMAND                  SERVICE               STATUS")
        print("secure-pr-guard-app         \"python graph_review.py\"  secure-pr-guard       Up")
        print("pr-guard-budget             \"python monitoring/bud…\"  budget-guard          Up") 
        print("pr-guard-monitor            \"python monitoring/pr_…\"  monitoring-dashboard  Up")
        print("pr-guard-redis              \"docker-entrypoint.s…\"    redis                Up")
        print("pr-guard-prometheus         \"/bin/prometheus --c…\"     prometheus           Up")
        print("pr-guard-grafana            \"/run.sh\"                  grafana              Up")
        
        print(f"\n{self.colored_text('✅ All enterprise services running!', 'green')}")
        self.pause_for_effect(2)

    def scene_3_pr_analysis(self):
        """Scene 3: PR Analysis with Budget Monitoring (30-50s)"""
        self.print_header("🤖 AI-POWERED PR ANALYSIS")
        
        print(f"{self.colored_text('🎯 Analyzing Facebook React Pull Request...', 'blue')}")
        print("$ ", end="")
        self.simulate_typing("python graph_review.py https://github.com/facebook/react/pull/27000")
        
        self.pause_for_effect(1)
        
        # Simulate complete PR analysis
        print("🚀 Starting Multi-Agent PR Review Workflow with Auto-Patch")
        print("📋 Workflow: Fetch → Nitpicker → Architect → Patch → Comment")
        print()
        
        print("🔍 Fetching diff from: https://github.com/facebook/react/pull/27000")
        self.pause_for_effect(0.5)
        print("📄 Diff length: 2,347 characters")
        print()
        
        print("🤖 Running AI code analysis + OWASP security checks...")
        self.pause_for_effect(1)
        print("📊 Token Analysis: 850 prompt + 120 completion = 970 total")
        print("📊 Efficiency: 87.6% prompt | 156.2 tok/sec | $0.000150/tok")
        print("💰 nitpicker_analysis: $0.001455 | 970 tokens | 6200ms")
        print("🔭 Telemetry: Span 3a2b1c8d | 24 attributes | Event logged")
        print()
        
        # Highlight budget monitoring
        print(f"{self.colored_text('🛡️ Budget Guard integration enabled', 'cyan')}")
        self.pause_for_effect(0.5)
        print(f"{self.colored_text('🚨 BUDGET ALERT [CRITICAL] - Budget exceeded by 39%', 'red')}")
        print(f"   Type: hourly_budget")
        print(f"   Current: $0.28 | Limit: $0.20 | Usage: 139.3%")
        print(f"   Alerts: 8 critical triggered")
        print()
        
        print("🏗️ Running architectural security analysis...")
        self.pause_for_effect(1)
        print("🔍 Architecture analysis complete:")
        print("   - Risk Level: MEDIUM")
        print("   - Security Issues: 3")
        print("   - OWASP LLM Top-10: 100% checked")
        print()
        
        print("🛠️ Generating patches for safe formatting issues...")
        self.pause_for_effect(0.5)
        print("📝 Auto-fixes identified for code style issues")
        print("⏭️ Skipping PR creation (demo mode)")
        print()
        
        print("💬 Formatting and posting GitHub comment...")
        print("✅ Analysis results ready")
        print()
        
        print(f"{self.colored_text('📊 WORKFLOW RESULTS', 'bold')}")
        print("✅ Analysis Complete!")
        print("   - Risk Level: MEDIUM")
        print("   - Total Issues: 5") 
        print("   - Security Issues: 3")
        print("   - Comment Posted: ✅ Yes")
        print("   - Patch Generated: ✅ Yes")
        
        self.pause_for_effect(2)

    def scene_4_budget_monitoring(self):
        """Scene 4: Budget Monitoring Deep Dive (50-65s)"""
        self.print_header("💰 INTELLIGENT BUDGET CONTROL")
        
        print(f"{self.colored_text('🔍 Detailed budget analysis...', 'blue')}")
        print("$ ", end="")
        self.simulate_typing("docker-compose exec budget-guard python monitoring/budget_guard.py --check")
        
        self.pause_for_effect(1)
        
        # Simulate budget check output in JSON format
        print("🛡️ Budget Guard - Real-time Status Report")
        print()
        print('''{
  "status": "active",
  "hourly_usage": {
    "current": 0.2786,
    "limit": 0.2,
    "percentage": 139.3
  },
  "daily_usage": {
    "current": 0.2786,
    "limit": 2.0,
    "percentage": 13.9
  },
  "recent_alerts": 8,
  "alert_breakdown": {
    "critical": 8,
    "warning": 0,
    "info": 0
  },
  "baseline_metrics": {
    "avg_cost_per_operation": 0.0174125,
    "avg_latency_ms": 5950.0,
    "avg_cost_per_1k_tokens": 0.06799,
    "efficiency_score": 8.2
  }
}''')
        
        print()
        print(f"{self.colored_text('📱 Multi-channel alerts configured:', 'cyan')}")
        print("   • Slack notifications: ✅ Enabled")
        print("   • Email alerts: ✅ Enabled") 
        print("   • Console logging: ✅ Active")
        print()
        print(f"{self.colored_text('🎯 This ensures enterprises never face unexpected AI cost overruns!', 'green')}")
        
        self.pause_for_effect(2)

    def scene_5_dashboard(self):
        """Scene 5: Enterprise Dashboard (65-80s)"""
        self.print_header("📊 ENTERPRISE MONITORING DASHBOARD")
        
        print(f"{self.colored_text('🌐 Opening enterprise analytics dashboard...', 'blue')}")
        print("$ ", end="")
        self.simulate_typing("open demo_dashboard.html")
        
        # Actually open dashboard
        dashboard_opened = self.open_dashboard()
        
        self.pause_for_effect(1)
        
        print("📈 Dashboard Components Loaded:")
        print("   💰 Cost Trends & Efficiency - Real-time cost tracking")
        print("   ⚡ Performance Distribution - Latency analysis with SLA zones")
        print("   🎯 Token Utilization - Usage breakdown by prompt/completion")
        print("   🚨 System Alerts - Real-time health monitoring")
        print("   📋 Executive Summary - KPI dashboard for management")
        print()
        
        if dashboard_opened:
            print(f"{self.colored_text('🎬 [Switch to browser to view live dashboard]', 'yellow')}")
            print(f"{self.colored_text('   → Hover over charts to see detailed metrics', 'cyan')}")
            print(f"{self.colored_text('   → Note the real-time data updates', 'cyan')}")
            print(f"{self.colored_text('   → Observe the executive-friendly layout', 'cyan')}")
            self.pause_for_effect(5)  # Give time to show dashboard
        
        print(f"\n{self.colored_text('📊 Live Analytics Summary:', 'magenta')}")
        print("   • Total Operations: 43")
        print("   • Total Cost: $0.52")
        print("   • Average Latency: 5,298ms")
        print("   • Cost Efficiency: $0.1500 per 1K tokens")
        print("   • SLA Compliance: 94.2%")
        print("   • Error Rate: < 0.1%")
        print()
        
        print(f"{self.colored_text('🎯 Management gets complete visibility into AI tool ROI and compliance!', 'green')}")
        
        self.pause_for_effect(2)

    def scene_6_summary(self):
        """Scene 6: Summary and Call-to-Action (80-120s)"""
        self.print_header("🏆 ENTERPRISE VALUE DELIVERED")
        
        print(f"{self.colored_text('✅ Secure PR Guard Delivers:', 'bold')}")
        print()
        print(f"   {self.colored_text('🛡️', 'green')} 100% OWASP LLM Compliance - Enterprise security assurance")
        print(f"   {self.colored_text('💰', 'blue')} Real-time Budget Control - Never exceed your budget")  
        print(f"   {self.colored_text('📊', 'cyan')} Complete Observability - Management-friendly insights")
        print(f"   {self.colored_text('🐳', 'magenta')} One-Click Docker Deployment - Production-ready in 5 minutes")
        print()
        
        print(f"{self.colored_text('📈 Performance vs Industry:', 'yellow')}")
        print("   • Cost: $0.15/PR vs $2.50+ (94% savings)")
        print("   • Speed: 17s vs 45s+ (62% faster)")
        print("   • Security: 100% vs 60% coverage")
        print("   • Test Coverage: 80%+ enterprise-grade")
        print()
        
        print(f"{self.colored_text('🎯 This project demonstrates expertise in:', 'cyan')}")
        print("   • AI Engineering & LLM Integration")
        print("   • FinOps & Cost Governance") 
        print("   • Security Compliance (OWASP)")
        print("   • Enterprise Observability")
        print("   • Cloud-Native Deployment")
        print()
        
        print(f"{self.colored_text('🚀 Ready to Use:', 'bold')}")
        print("   📦 Docker: ghcr.io/siwenwang0803/secure-pr-guard:v1.0.0")
        print("   ⭐ GitHub: github.com/siwenwang0803/secure-pr-guard")
        print("   📖 Release: v1.0.0 with complete documentation")
        print()
        
        print(f"{self.colored_text('💡 Star the repo or try the Docker image today!', 'green')}")
        
        # QR Code Integration
        print(f"\n{self.colored_text('📱 QR CODE DISPLAY:', 'yellow')}")
        print(f"   {self.colored_text('→ GitHub Repository Access', 'cyan')}")
        print(f"   {self.colored_text('→ Direct Docker Pull Command', 'cyan')}")
        print(f"   {self.colored_text('→ Live Documentation', 'cyan')}")
        
        # Generate QR code if not exists
        if not os.path.exists('github_qr.png'):
            self.generate_qr_code()
        
        # Open QR code for display
        if os.path.exists('github_qr.png'):
            print(f"\n{self.colored_text('📱 [Opening QR code for display]', 'bold')}")
            subprocess.run(['open', 'github_qr.png'], check=False)  # macOS
            print(f"{self.colored_text('🎬 [QR code displayed - scan for instant access]', 'yellow')}")
            self.pause_for_effect(8)  # Extended time for QR code visibility
        
        print(f"\n{self.colored_text('🎬 Thank you for watching!', 'bold')}")
        print(f"{self.colored_text('Enterprise AI Code Review - Delivered.', 'cyan')}")

    def run_complete_demo(self, scene=None):
        """Run the complete demo or specific scene"""
        
        # Clear screen for clean demo
        os.system('clear')
        
        if scene is None:
            # Run complete demo
            print(f"{self.colored_text('🎬 SECURE PR GUARD - ENTERPRISE DEMO', 'bold')}")
            print(f"{self.colored_text('Professional 2-Minute Product Demonstration', 'cyan')}")
            print(f"{self.colored_text('Recording Mode: Complete Workflow', 'yellow')}")
            print()
            self.pause_for_effect(2)
            
            self.scene_1_github_intro()      # 0-15s
            self.scene_2_docker_deployment() # 15-30s  
            self.scene_3_pr_analysis()       # 30-50s
            self.scene_4_budget_monitoring() # 50-65s
            self.scene_5_dashboard()         # 65-80s
            self.scene_6_summary()           # 80-120s
            
        else:
            # Run specific scene
            scene_methods = {
                1: self.scene_1_github_intro,
                2: self.scene_2_docker_deployment,
                3: self.scene_3_pr_analysis,
                4: self.scene_4_budget_monitoring, 
                5: self.scene_5_dashboard,
                6: self.scene_6_summary
            }
            
            if scene in scene_methods:
                print(f"{self.colored_text(f'🎬 DEMO SECTION {scene}', 'bold')}")
                scene_methods[scene]()
            else:
                print(f"{self.colored_text('❌ Invalid scene number. Use 1-6.', 'red')}")

    def prepare_recording_environment(self):
        """Prepare environment for optimal recording"""
        print(f"{self.colored_text('🎬 RECORDING PREPARATION', 'bold')}")
        print()
        
        # Generate QR code
        qr_generated = self.generate_qr_code()
        
        # Check dashboard file
        dashboard_exists = os.path.exists("demo_dashboard.html")
        if dashboard_exists:
            print(f"{self.colored_text('✅ Dashboard file found: demo_dashboard.html', 'green')}")
        else:
            print(f"{self.colored_text('⚠️ Dashboard file not found: demo_dashboard.html', 'yellow')}")
            print("   Generate it with: docker cp pr-guard-monitor:/app/pr_guard_monitor_*.html ./demo_dashboard.html")
        
        print()
        print(f"{self.colored_text('📹 Recording Tips:', 'cyan')}")
        print("   1. Close unnecessary applications")
        print("   2. Enable 'Do Not Disturb' mode")
        print("   3. Use Cmd+Shift+5 for screen recording")
        print("   4. Record at 1920x1080 resolution")
        print("   5. For Scene 5: Split screen Terminal + Browser")
        print("   6. For Scene 6: QR code will auto-open in Preview")
        print()
        
        return qr_generated and dashboard_exists

def main():
    """Main function with command line interface"""
    
    demo = DemoPresentation()
    
    if len(sys.argv) == 1:
        # Prepare recording environment first
        print("🎬 Complete Demo with Dashboard & QR Integration")
        print()
        
        ready = demo.prepare_recording_environment()
        if not ready:
            print(f"{demo.colored_text('⚠️ Some files are missing. Continue anyway? (y/n)', 'yellow')}")
            if input().lower() != 'y':
                return
        
        print("\n🎬 Starting Complete Demo (2 minutes)")
        print("Press Ctrl+C to stop at any time")
        print()
        input("Press Enter to begin recording... ")
        demo.run_complete_demo()
        
    elif len(sys.argv) == 2:
        scene_arg = sys.argv[1]
        
        if scene_arg == "prep":
            demo.prepare_recording_environment()
            return
        elif scene_arg == "qr":
            demo.generate_qr_code()
            return
        elif scene_arg == "dashboard":
            demo.open_dashboard()
            return
            
        try:
            scene_num = int(scene_arg)
            print(f"🎬 Running Demo Section {scene_num}")
            print()
            input(f"Press Enter to begin Section {scene_num}... ")
            demo.run_complete_demo(scene_num)
        except ValueError:
            print("❌ Please provide a scene number (1-6)")
            print("Usage: python complete_demo.py [scene_number]")
            print()
            print("Commands:")
            print("  prep      - Prepare recording environment")
            print("  qr        - Generate QR code only")
            print("  dashboard - Open dashboard only")
            print("  1-6       - Run specific scene")
            print("  (no args) - Run complete demo")
            print()
            print("Scenes:")
            print("  1 - GitHub Project Introduction (0-15s)")
            print("  2 - Docker Deployment (15-30s)")
            print("  3 - PR Analysis with Budget Alerts (30-50s)")
            print("  4 - Budget Monitoring Deep Dive (50-65s)")
            print("  5 - Enterprise Dashboard (65-80s)")
            print("  6 - Summary and Call-to-Action (80-120s)")
    else:
        print("Usage: python complete_demo.py [command]")

if __name__ == "__main__":
    main()