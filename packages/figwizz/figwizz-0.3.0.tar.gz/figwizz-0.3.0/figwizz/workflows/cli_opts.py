"""
Command-line interface for FigWizz
"""

import argparse
import sys
from pathlib import Path


def create_parser():
    """Create the main CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog='figwizz',
        description='FigWizz - Python toolkit for programmatic figure design',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Global options
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--env-file', type=str, default='auto',
                       help='Path to .env file (default: auto-detect)')
    
    # Create subparsers
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # download-stock command
    parser_stock = subparsers.add_parser(
        'download-stock',
        help='Download stock images from Pixabay or Unsplash'
    )
    parser_stock.add_argument('query', type=str,
                             help='Search query for images')
    parser_stock.add_argument('-n', '--n-images', type=int, default=10,
                             help='Number of images to download (default: 10)')
    parser_stock.add_argument('-o', '--output-dir', type=str, default='stock_images',
                             help='Output directory (default: stock_images)')
    parser_stock.add_argument('-p', '--provider', type=str, default='unsplash',
                             choices=['pixabay', 'unsplash'],
                             help='Image provider (default: unsplash)')
    parser_stock.add_argument('--api-key', type=str, default=None,
                             help='API key (or set via environment)')
    
    # generate command
    parser_gen = subparsers.add_parser(
        'generate',
        help='Generate images using AI models'
    )
    parser_gen.add_argument('prompts', type=str, nargs='+',
                           help='Text prompts for image generation')
    parser_gen.add_argument('-n', '--n-images', type=int, default=1,
                           help='Number of images per prompt (default: 1)')
    parser_gen.add_argument('-o', '--output-dir', type=str, default='generated',
                           help='Output directory (default: generated)')
    parser_gen.add_argument('-m', '--model', type=str, default='dall-e-3',
                           help='AI model to use (default: dall-e-3)')
    parser_gen.add_argument('--api-key', type=str, default=None,
                           help='API key (or set via environment)')
    
    # slides-to-images command
    parser_slides = subparsers.add_parser(
        'slides-to-images',
        help='Convert presentation slides to images'
    )
    parser_slides.add_argument('input', type=str,
                              help='Path to presentation file (.pptx, .ppt, .key)')
    parser_slides.add_argument('-o', '--output-dir', type=str, default='slides',
                              help='Output directory (default: slides)')
    parser_slides.add_argument('-f', '--format', type=str, default='figure{:02d}.png',
                              help='Filename format (default: figure{:02d}.png)')
    parser_slides.add_argument('--no-crop', action='store_true',
                              help='Disable automatic cropping')
    parser_slides.add_argument('--margin', type=str, default='1cm',
                              help='Margin size after cropping (default: 1cm)')
    parser_slides.add_argument('--dpi', type=int, default=300,
                              help='Output DPI (default: 300)')
    
    # extract-pdf command
    parser_pdf = subparsers.add_parser(
        'extract-pdf',
        help='Extract images from PDF files'
    )
    parser_pdf.add_argument('input', type=str,
                           help='Path to PDF file')
    parser_pdf.add_argument('-o', '--output-dir', type=str, default='extracted',
                           help='Output directory (default: extracted)')
    parser_pdf.add_argument('--min-width', type=int, default=100,
                           help='Minimum image width (default: 100)')
    parser_pdf.add_argument('--min-height', type=int, default=100,
                           help='Minimum image height (default: 100)')
    parser_pdf.add_argument('--prefix', type=str, default='figure',
                           help='Filename prefix (default: figure)')
    
    # extract-url command
    parser_url = subparsers.add_parser(
        'extract-url',
        help='Extract images from web URLs'
    )
    parser_url.add_argument('url', type=str,
                           help='URL to extract images from')
    parser_url.add_argument('-o', '--output-dir', type=str, default='web_images',
                           help='Output directory (default: web_images)')
    parser_url.add_argument('--min-width', type=int, default=100,
                           help='Minimum image width (default: 100)')
    parser_url.add_argument('--min-height', type=int, default=100,
                           help='Minimum image height (default: 100)')
    parser_url.add_argument('--prefix', type=str, default='image',
                           help='Filename prefix (default: image)')
    parser_url.add_argument('--convert-svg', action='store_true',
                           help='Convert SVG files to PNG')
    parser_url.add_argument('--svg-scale', type=float, default=3.0,
                           help='SVG scaling factor (default: 3.0)')
    
    return parser


def cmd_download_stock(args):
    """Execute download-stock command."""
    from figwizz import download_stock_images
    
    if args.verbose:
        print(f"Downloading {args.n_images} images from {args.provider}...")
        print(f"Query: {args.query}")
    
    try:
        images = download_stock_images(
            query=args.query,
            n_images=args.n_images,
            output_dir=args.output_dir,
            provider=args.provider,
            api_key=args.api_key
        )
        print(f"Successfully downloaded {len(images)} images to {args.output_dir}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_generate(args):
    """Execute generate command."""
    from figwizz.generate import generate_images
    
    if args.verbose:
        print(f"Generating images with {args.model}...")
        print(f"Prompts: {args.prompts}")
    
    try:
        images = generate_images(
            prompts=args.prompts,
            output_dir=args.output_dir,
            n_images=args.n_images,
            model=args.model,
            api_key=args.api_key,
            return_images=False
        )
        print(f"Successfully generated images in {args.output_dir}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_slides_to_images(args):
    """Execute slides-to-images command."""
    from figwizz import slides_to_images
    
    if args.verbose:
        print(f"Converting slides from {args.input}...")
    
    try:
        slides_to_images(
            input_path=args.input,
            output_path=args.output_dir,
            filename_format=args.format,
            crop_images=not args.no_crop,
            margin_size=args.margin,
            dpi=args.dpi
        )
        print(f"Successfully converted slides to {args.output_dir}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_extract_pdf(args):
    """Execute extract-pdf command."""
    from figwizz import extract_images_from_pdf
    
    if args.verbose:
        print(f"Extracting images from {args.input}...")
    
    try:
        images = extract_images_from_pdf(
            pdf_path=args.input,
            output_dir=args.output_dir,
            min_width=args.min_width,
            min_height=args.min_height,
            name_prefix=args.prefix
        )
        print(f"Successfully extracted {len(images)} images to {args.output_dir}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_extract_url(args):
    """Execute extract-url command."""
    from figwizz import extract_images_from_url, is_url_a_pdf
    from figwizz import download_pdf_from_url, extract_images_from_pdf
    
    if args.verbose:
        print(f"Extracting images from {args.url}...")
    
    try:
        # Check if URL is a PDF
        if is_url_a_pdf(args.url):
            if args.verbose:
                print("Detected PDF URL, downloading...")
            pdf_path = download_pdf_from_url(args.url)
            images = extract_images_from_pdf(
                pdf_path=pdf_path,
                output_dir=args.output_dir,
                min_width=args.min_width,
                min_height=args.min_height,
                name_prefix=args.prefix
            )
            # Clean up temp PDF
            Path(pdf_path).unlink()
        else:
            images = extract_images_from_url(
                url=args.url,
                output_dir=args.output_dir,
                min_width=args.min_width,
                min_height=args.min_height,
                name_prefix=args.prefix,
                convert_svg=args.convert_svg,
                svg_scale=args.svg_scale
            )
        
        print(f"Successfully extracted {len(images)} images to {args.output_dir}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # If no command provided, show help
    if args.command is None:
        parser.print_help()
        return 0
    
    # Load environment file if specified
    if args.env_file and args.env_file != 'auto':
        from figwizz.utils import load_env_variables
        try:
            load_env_variables(args.env_file)
            if args.verbose:
                print(f"Loaded environment from {args.env_file}")
        except Exception as e:
            if args.verbose:
                print(f"Warning: Could not load environment file: {e}")
    
    # Execute command
    command_map = {
        'download-stock': cmd_download_stock,
        'generate': cmd_generate,
        'slides-to-images': cmd_slides_to_images,
        'extract-pdf': cmd_extract_pdf,
        'extract-url': cmd_extract_url,
    }
    
    cmd_func = command_map.get(args.command)
    if cmd_func:
        return cmd_func(args)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())

