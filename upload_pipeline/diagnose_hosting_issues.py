"""
Diagnose hosting URL issues and provide solutions
Tests connectivity, DNS resolution, and URL accessibility
"""
import requests
import socket
import sys
import os
from urllib.parse import urlparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_manager import db_manager


class HostingDiagnostics:
    def __init__(self):
        self.hosts_to_test = {
            'streamtape': 'https://streamtape.com',
            'vidoza': 'https://vidoza.net',
            'turboviplay': 'https://turboviplay.com',
            'seekstreaming': 'https://seekstreaming.com'
        }
        
    def test_dns_resolution(self, hostname):
        """Test if DNS can resolve the hostname"""
        try:
            ip = socket.gethostbyname(hostname)
            return True, ip
        except socket.gaierror:
            return False, "DNS resolution failed"
    
    def test_connectivity(self, url, timeout=10):
        """Test basic connectivity to URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            return True, response.status_code, response.elapsed.total_seconds()
        except requests.exceptions.Timeout:
            return False, "Timeout", None
        except requests.exceptions.ConnectionError as e:
            return False, f"Connection Error: {str(e)[:100]}", None
        except Exception as e:
            return False, f"Error: {str(e)[:100]}", None
    
    def diagnose_all_hosts(self):
        """Run diagnostics on all hosting services"""
        print("="*80)
        print("HOSTING SERVICE DIAGNOSTICS")
        print("="*80)
        
        results = {}
        
        for host_name, base_url in self.hosts_to_test.items():
            print(f"\n[{host_name.upper()}]")
            print(f"Base URL: {base_url}")
            
            # Parse hostname
            hostname = urlparse(base_url).netloc
            
            # Test DNS
            dns_ok, dns_result = self.test_dns_resolution(hostname)
            if dns_ok:
                print(f"  ✓ DNS Resolution: {dns_result}")
            else:
                print(f"  ✗ DNS Resolution: {dns_result}")
                results[host_name] = {'status': 'dns_failed', 'issue': dns_result}
                continue
            
            # Test connectivity
            conn_ok, status, elapsed = self.test_connectivity(base_url, timeout=15)
            if conn_ok:
                print(f"  ✓ Connectivity: HTTP {status} ({elapsed:.2f}s)")
                results[host_name] = {'status': 'working', 'http_status': status}
            else:
                print(f"  ✗ Connectivity: {status}")
                results[host_name] = {'status': 'connection_failed', 'issue': status}
        
        return results
    
    def test_video_urls(self):
        """Test actual video URLs from database"""
        print("\n" + "="*80)
        print("VIDEO URL TESTING")
        print("="*80)
        
        videos = db_manager.get_all_videos()
        
        if not videos:
            print("\n⚠️  No videos found in database")
            return
        
        for video in videos:
            code = video.get('code', 'Unknown')
            print(f"\n[{code}]")
            
            if 'hosting_urls' not in video or not video['hosting_urls']:
                print("  ⚠️  No hosting URLs")
                continue
            
            for host, urls in video['hosting_urls'].items():
                embed_url = urls.get('embed_url', '')
                file_code = urls.get('file_code', '')
                
                if not embed_url:
                    continue
                
                print(f"\n  {host.upper()}:")
                print(f"    File Code: {file_code}")
                print(f"    URL: {embed_url}")
                
                # Test URL
                conn_ok, status, elapsed = self.test_connectivity(embed_url, timeout=15)
                if conn_ok:
                    print(f"    ✓ Status: HTTP {status} ({elapsed:.2f}s)")
                else:
                    print(f"    ✗ Status: {status}")
    
    def provide_solutions(self, results):
        """Provide solutions based on diagnostic results"""
        print("\n" + "="*80)
        print("RECOMMENDATIONS")
        print("="*80)
        
        failed_hosts = [host for host, data in results.items() if data['status'] != 'working']
        working_hosts = [host for host, data in results.items() if data['status'] == 'working']
        
        if not failed_hosts:
            print("\n✓ All hosting services are accessible!")
            print("\nIf videos still don't play, the issue might be:")
            print("  1. Invalid file codes (files deleted from host)")
            print("  2. Embed restrictions (some hosts block certain referrers)")
            print("  3. Browser/player compatibility issues")
            return
        
        print(f"\n⚠️  {len(failed_hosts)} hosting service(s) not accessible:")
        for host in failed_hosts:
            print(f"  - {host}: {results[host]['issue']}")
        
        print(f"\n✓ {len(working_hosts)} hosting service(s) working:")
        for host in working_hosts:
            print(f"  - {host}")
        
        print("\n" + "-"*80)
        print("POSSIBLE CAUSES:")
        print("-"*80)
        
        if any('Timeout' in str(results[h].get('issue', '')) for h in failed_hosts):
            print("\n1. NETWORK/ISP BLOCKING")
            print("   - Your ISP might be blocking these video hosting sites")
            print("   - Try using a VPN or proxy")
            print("   - Check if sites are accessible in your browser")
        
        if any('DNS' in str(results[h].get('issue', '')) for h in failed_hosts):
            print("\n2. DNS ISSUES")
            print("   - DNS servers cannot resolve these domains")
            print("   - Try changing DNS to 8.8.8.8 (Google) or 1.1.1.1 (Cloudflare)")
        
        if any('Connection' in str(results[h].get('issue', '')) for h in failed_hosts):
            print("\n3. FIREWALL/PROXY")
            print("   - Corporate firewall or proxy might be blocking")
            print("   - Check Windows Firewall settings")
            print("   - Try disabling VPN if active")
        
        print("\n" + "-"*80)
        print("SOLUTIONS:")
        print("-"*80)
        
        print("\n1. USE WORKING HOSTS ONLY")
        print("   - Focus on uploading to working hosts:")
        for host in working_hosts:
            print(f"     • {host}")
        
        print("\n2. TEST IN BROWSER")
        print("   - Open these URLs in your browser to verify:")
        for host in failed_hosts:
            if host in self.hosts_to_test:
                print(f"     • {self.hosts_to_test[host]}")
        
        print("\n3. USE VPN/PROXY")
        print("   - If sites are blocked, use a VPN service")
        print("   - Configure proxy in upload scripts")
        
        print("\n4. ALTERNATIVE HOSTS")
        print("   - Consider using only accessible hosts")
        print("   - Update upload pipeline to skip blocked hosts")
        
        print("\n" + "="*80 + "\n")


def main():
    diagnostics = HostingDiagnostics()
    
    # Run diagnostics
    results = diagnostics.diagnose_all_hosts()
    
    # Test actual video URLs
    diagnostics.test_video_urls()
    
    # Provide solutions
    diagnostics.provide_solutions(results)


if __name__ == "__main__":
    main()
