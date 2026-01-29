"""
Main Diagnosis Orchestrator for NetworkDoctor
"""
import asyncio
from typing import List, Dict, Any, Optional
from networkdoctor.core.scanner import NetworkScanner
from networkdoctor.core.analyzer import NetworkAnalyzer
from networkdoctor.core.intelligence import IntelligenceEngine
from networkdoctor.utils.cache_manager import CacheManager
from networkdoctor.cli.validator import validate_targets
from networkdoctor.cli.progress import ProgressManager


class NetworkDoctor:
    """Main orchestrator for network diagnosis"""
    
    def __init__(self, use_cache: bool = True):
        """
        Initialize NetworkDoctor.
        
        Args:
            use_cache: Enable result caching
        """
        self.scanner = NetworkScanner()
        self.analyzer = NetworkAnalyzer()
        self.intelligence = IntelligenceEngine()
        self.cache = CacheManager() if use_cache else None
        self.doctors = self._load_doctors()
    
    def _load_doctors(self) -> Dict[str, Any]:
        """Load all doctor modules"""
        doctors = {}
        
        # Import doctor modules
        try:
            from networkdoctor.modules import dns_doctor
            doctors["dns"] = dns_doctor.DNSDoctor()
        except Exception:
            pass
        
        try:
            from networkdoctor.modules import firewall_detector
            doctors["firewall"] = firewall_detector.FirewallDetector()
        except Exception:
            pass
        
        try:
            from networkdoctor.modules import performance_analyst
            doctors["performance"] = performance_analyst.PerformanceAnalyst()
        except Exception:
            pass
        
        try:
            from networkdoctor.modules import security_inspector
            doctors["security"] = security_inspector.SecurityInspector()
        except Exception:
            pass
        
        try:
            from networkdoctor.modules import ssl_tls_checker
            doctors["ssl"] = ssl_tls_checker.SSLChecker()
        except Exception:
            pass
        
        try:
            from networkdoctor.modules import routing_expert
            doctors["routing"] = routing_expert.RoutingExpert()
        except Exception:
            pass
        
        try:
            from networkdoctor.modules import wifi_diagnoser
            doctors["wifi"] = wifi_diagnoser.WiFiDiagnoser()
        except Exception:
            pass
        
        try:
            from networkdoctor.modules import cloud_network_doctor
            doctors["cloud"] = cloud_network_doctor.CloudNetworkDoctor()
        except Exception:
            pass
        
        try:
            from networkdoctor.modules import voip_quality_analyst
            doctors["voip"] = voip_quality_analyst.VoIPQualityAnalyst()
        except Exception:
            pass
        
        try:
            from networkdoctor.modules import application_layer_doctor
            doctors["application"] = application_layer_doctor.ApplicationLayerDoctor()
        except Exception:
            pass
        
        try:
            from networkdoctor.modules import enterprise_network_doctor
            doctors["enterprise"] = enterprise_network_doctor.EnterpriseNetworkDoctor()
        except Exception:
            pass
        
        try:
            from networkdoctor.modules import iot_network_checker
            doctors["iot"] = iot_network_checker.IoTNetworkChecker()
        except Exception:
            pass
        
        try:
            from networkdoctor.modules import cable_fiber_analyst
            doctors["physical"] = cable_fiber_analyst.CableFiberAnalyst()
        except Exception:
            pass
        
        try:
            from networkdoctor.modules import network_capacity_planner
            doctors["capacity"] = network_capacity_planner.NetworkCapacityPlanner()
        except Exception:
            pass
        
        try:
            from networkdoctor.modules import protocol_analyst
            doctors["protocol"] = protocol_analyst.ProtocolAnalyst()
        except Exception:
            pass
        
        # New modules added for unique features
        try:
            from networkdoctor.modules import isp_throttle_detector
            doctors["isp_throttle"] = isp_throttle_detector.ISPThrottleDetector()
        except Exception:
            pass
        
        try:
            from networkdoctor.modules import smart_route_analyzer
            doctors["route_analyzer"] = smart_route_analyzer.SmartRouteAnalyzer()
        except Exception:
            pass
        
        try:
            from networkdoctor.modules import auto_network_repair
            doctors["auto_repair"] = auto_network_repair.AutoNetworkRepair()
        except Exception:
            pass
        
        try:
            from networkdoctor.modules import server_self_heal
            doctors["server_heal"] = server_self_heal.ServerSelfHeal()
        except Exception:
            pass
        
        try:
            from networkdoctor.modules import internet_quality_score
            doctors["quality_score"] = internet_quality_score.InternetQualityScore()
        except Exception:
            pass
        
        try:
            from networkdoctor.modules import ai_root_cause
            doctors["root_cause"] = ai_root_cause.AIRootCauseEngine()
        except Exception:
            pass
        
        try:
            from networkdoctor.modules import offline_diagnosis
            doctors["offline"] = offline_diagnosis.OfflineDiagnosis()
        except Exception:
            pass
        
        try:
            from networkdoctor.modules import predictive_failure
            doctors["predictive"] = predictive_failure.PredictiveFailureAlert()
        except Exception:
            pass
        
        return doctors
    
    async def diagnose(
        self,
        targets: List[str],
        doctors: Optional[List[str]] = None,
        skip_doctors: Optional[List[str]] = None,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Perform network diagnosis.
        
        Args:
            targets: List of target strings
            doctors: Optional list of doctor names to run
            skip_doctors: Optional list of doctor names to skip
            verbose: Enable verbose output
            
        Returns:
            Complete diagnosis results
        """
        # Validate targets
        validated_targets = validate_targets(targets)
        
        # Expand targets (handle CIDR, files, etc.)
        expanded_targets = self.scanner.expand_targets(targets)
        
        # Determine which doctors to run
        doctors_to_run = self._select_doctors(doctors, skip_doctors)
        
        # Scan network
        with ProgressManager(verbose=verbose) as progress:
            progress.print("🔍 Scanning network...", style="cyan")
            scan_results = await self.scanner.scan_targets(expanded_targets)
        
        # Run doctors
        doctor_results = []
        for doctor_name, doctor_instance in doctors_to_run.items():
            # Create unique cache key from all targets and scan results hash
            import hashlib
            targets_str = "_".join(sorted(targets))
            scan_hash = hashlib.md5(str(scan_results).encode()).hexdigest()[:8]
            cache_key = f"{targets_str}_{scan_hash}"
            
            if self.cache:
                # Try cache first
                cached = self.cache.get(cache_key, doctor_name)
                if cached and not verbose:  # Skip cache in verbose mode
                    doctor_results.append(cached)
                    continue
            
            try:
                result = await doctor_instance.diagnose(scan_results)
                doctor_results.append(result)
                
                if self.cache:
                    self.cache.set(cache_key, doctor_name, result)
            except Exception as e:
                if verbose:
                    print(f"Error in {doctor_name}: {e}")
                continue
        
        # Analyze results
        analysis = self.analyzer.analyze_results(scan_results, doctor_results)
        
        # Apply intelligence
        intelligence = self.intelligence.analyze_issues(
            analysis["issues"],
            {"scan_results": scan_results}
        )
        
        return {
            "targets": targets,
            "scan_results": scan_results,
            "doctor_results": doctor_results,
            "analysis": analysis,
            "intelligence": intelligence,
        }
    
    def _select_doctors(
        self,
        doctors: Optional[List[str]],
        skip_doctors: Optional[List[str]]
    ) -> Dict[str, Any]:
        """
        Select which doctors to run.
        
        Args:
            doctors: List of doctor names to run
            skip_doctors: List of doctor names to skip
            
        Returns:
            Dictionary of selected doctors
        """
        if doctors:
            return {name: self.doctors[name] for name in doctors if name in self.doctors}
        
        selected = self.doctors.copy()
        
        if skip_doctors:
            for name in skip_doctors:
                selected.pop(name, None)
        
        return selected
    
    def run(self, args) -> int:
        """
        Run NetworkDoctor with command line arguments.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Exit code
        """
        try:
            # Determine doctors to run
            doctors = None
            if args.doctors:
                doctors = [d.strip() for d in args.doctors.split(",")]
            
            skip_doctors = None
            if args.skip:
                skip_doctors = [d.strip() for d in args.skip.split(",")]
            
            # Run diagnosis
            results = asyncio.run(
                self.diagnose(
                    targets=args.targets,
                    doctors=doctors,
                    skip_doctors=skip_doctors,
                    verbose=args.verbose
                )
            )
            
            # Output results based on format
            output_format = getattr(args, 'output', 'terminal')
            output_file = getattr(args, 'output_file', None)
            
            if output_format == "terminal":
                from networkdoctor.outputs.terminal_display import TerminalDisplay
                display = TerminalDisplay()
                display.show_results(results, verbose=args.verbose)
            elif output_format == "html":
                from networkdoctor.outputs.html_reporter import HTMLReporter
                if output_file:
                    HTMLReporter.generate(results, output_file)
                else:
                    HTMLReporter.generate(results)
            elif output_format == "json":
                from networkdoctor.outputs.json_exporter import JSONExporter
                if output_file:
                    JSONExporter.export(results, output_file)
                else:
                    JSONExporter.export(results)
            elif output_format == "pdf":
                from networkdoctor.outputs.pdf_reporter import PDFReporter
                if output_file:
                    PDFReporter.generate(results, output_file)
                else:
                    PDFReporter.generate(results)
            elif output_format == "csv":
                from networkdoctor.outputs.csv_exporter import CSVExporter
                if output_file:
                    CSVExporter.export(results, output_file)
                else:
                    CSVExporter.export(results)
            elif output_format == "markdown":
                from networkdoctor.outputs.markdown_generator import MarkdownGenerator
                if output_file:
                    MarkdownGenerator.generate(results, output_file)
                else:
                    MarkdownGenerator.generate(results)
            
            return 0
        except Exception as e:
            print(f"Error: {e}")
            return 1

