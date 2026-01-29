import argparse
import os
import sys
from loguru import logger
import warnings

# Add the project root (parent directory of 'autodg' folder) to sys.path
# This allows running 'python autodg/main.py' directly without PYTHONPATH=.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root_dir = os.path.dirname(current_dir)
if project_root_dir not in sys.path:
    sys.path.insert(0, project_root_dir)

warnings.filterwarnings("ignore", category=SyntaxWarning)
from autodg.modules.orchestration.dispatcher import Dispatcher
from autodg.modules.orchestration.resolver import Resolver
from autodg.modules.output.write_files import MarkdownGenerator
from autodg.modules.core.llm import LLMClient
from autodg.modules.analysis.changelog_generator import ChangelogGenerator


def main():
    parser = argparse.ArgumentParser(description="Python API Analyzer")
    parser.add_argument("--paths", required=True, help="Path to the project root")
    parser.add_argument("--output", default="output", help="Output directory")
    parser.add_argument(
        "--ollama", type=bool, default=False, help="Enable Ollama LLM explanations"
    )
    parser.add_argument(
        "--doc-type",
        choices=["file", "request", "both"],
        default="both",
        help="Type of documentation to generate",
    )
    parser.add_argument(
        "--gen-devops",
        action="store_true",
        help="Generate Scaling and Deployment documents",
    )
    parser.add_argument(
        "--gen-features",
        action="store_true",
        help="Generate Feature-wise docs and User Stories",
    )
    parser.add_argument(
        "--gen-changelog",
        action="store_true",
        help="Generate Automated Changelog (AI Summary)",
    )

    args = parser.parse_args()

    project_root = os.path.abspath(args.paths)
    output_dir = os.path.abspath(args.output)

    if not os.path.exists(project_root):
        print(f"Error: Project path {project_root} does not exist.")
        sys.exit(1)

    print(f"Starting analysis on: {project_root}")

    # 1. Dispatcher - Detect and Extract
    dispatcher = Dispatcher(project_root)
    dispatcher.detect_frameworks()
    routes = dispatcher.run()

    print(f"Extracted {len(routes)} routes.")
    
    # Setup Logging (Loguru)
    log_file = os.path.join(output_dir, "aidocs_generation.log")
    logger.remove()  # Remove default handler
    logger.add(sys.stderr, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")
    logger.add(log_file, rotation="10 MB", level="INFO", format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}")
    
    logger.info(f"Started analysis session for: {project_root}")
    logger.info(f"Extracted {len(routes)} routes.")

    # 2. Setup LLM Client if enabled
    llm_client = None
    if args.ollama:
        print("\n" + "=" * 60)
        print("                   AUTODG EXECUTION PLAN                   ")
        print("=" * 60)
        print(f"Target Project:   {project_root}")
        print(f"Output Directory: {os.path.abspath(output_dir)}")
        print(f"Routes Found:     {len(routes)}")
        print("AI Provider:      Ollama (Local)")
        print("-" * 60)
        
        print("Folders to be Created:")
        print(f"  • {os.path.join(output_dir, 'request_docs')}/")
        if args.doc_type in ["file", "both"]:
            print(f"  • {os.path.join(output_dir, 'file_docs')}/")

        print("\nDocuments to be Generated:")
        print(f"  • [Technical] API Route Documentation ({len(routes)} files)")
        if args.gen_features:
            print("  • [Business]  features_and_stories.md")
        if args.gen_devops:
            print("  • [DevOps]    scaling_guide.md")
            print("  • [DevOps]    deployment_guide.md")
        if args.gen_changelog:
            print("  • [General]   changelog.md")
        print("-" * 60)
        
        # Log Plan
        logger.info("Execution Plan:")
        logger.info(f"Target: {project_root}")
        logger.info(f"Artifacts: Technical Docs, AI Audits, Features={args.gen_features}, DevOps={args.gen_devops}, Changelog={args.gen_changelog}")

        if len(routes) > 50:
            warn_msg = f"WARNING: AI analysis for {len(routes)} routes is resource-intensive."
            est_time = f"Estimated time: ~{len(routes) * 5 / 60:.1f} to {len(routes) * 10 / 60:.1f} minutes."
            print(f"{warn_msg}")
            print(f"{est_time}")
        
        confirm = input("\nProceed with AI Analysis? (y/n): ")
        if confirm.lower() != "y":
            print("Skipping AI features. Generating basic static documentation only...")
            args.ollama = False
            args.gen_features = False
            args.gen_devops = False
            args.gen_changelog = False
        else:
            llm_client = LLMClient()

    # 3. Resolver - Enrich
    try:
        Resolver.resolve(routes, project_root, llm_client=llm_client)
    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted by user. Saving partial results...")

    # 4. Output - Generate Docs
    generator = MarkdownGenerator(output_dir, use_llm=args.ollama)
    if llm_client:
        generator.llm_client = llm_client

    if args.doc_type in ["request", "both"]:
        generator.generate_route_docs(routes)

    if args.doc_type in ["file", "both"]:
        generator.generate_file_docs(project_root)

    # 5. Specialized Docs
    if llm_client:
        if args.gen_features:
            print("Generating Feature-wise docs and User Stories...")
            from autodg.modules.analysis.feature_analyzer import FeatureAnalyzer

            fe_analyzer = FeatureAnalyzer(llm_client)
            content = fe_analyzer.generate_feature_docs(routes)
            with open(os.path.join(output_dir, "features_and_stories.md"), "w") as f:
                f.write(content)

        if args.gen_devops:
            print("Generating Scaling and Deployment documents...")
            from autodg.modules.analysis.dev_ops_generator import DevOpsGenerator

            devops = DevOpsGenerator(llm_client)
            scaling = devops.generate_scaling_doc(routes)
            deployment = devops.generate_deployment_doc(routes, project_root)
            with open(os.path.join(output_dir, "scaling_guide.md"), "w") as f:
                f.write(scaling)
            with open(os.path.join(output_dir, "deployment_guide.md"), "w") as f:
                f.write(deployment)

        if args.gen_changelog:
            print("Generating Automated Changelog...")
            chan_gen = ChangelogGenerator(llm_client)
            changelog_content = chan_gen.generate(routes)
            with open(os.path.join(output_dir, "changelog.md"), "w") as f:
                f.write(changelog_content)

    print(f"Analysis complete. Output saved to {output_dir}")


if __name__ == "__main__":
    main()
