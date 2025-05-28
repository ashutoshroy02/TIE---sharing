import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import threading
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib import patches
import numpy as np
from PIL import Image
import os
import json
import logging # Import logging
import traceback # Import traceback
from layout_model import process_files, process_single_page, LayoutProcessor
from surya.layout import LayoutPredictor
from pathlib import Path
from datetime import datetime

# Set up logging for the GUI script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize the Surya layout predictor (assuming it's thread-safe or handled)
# Note: Initializing here might not be ideal if it's not thread-safe and used in processing thread
# Consider initializing it within the processing thread if it causes issues.
try:
    layout_predictor = LayoutPredictor()
    logger.info("Surya model loaded successfully in GUI.")
except ImportError:
    logger.error("Surya model not found. Please install it using: pip install surya. Layout analysis will not work.")
    layout_predictor = None
except Exception as e:
    logger.error(f"Error loading Surya model in GUI: {str(e)}")
    layout_predictor = None


class LayoutAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Document Layout Analyzer")
        self.root.geometry("1200x800")
        
        # Initialize variables
        self.current_page = 0
        self.images = []
        self.regions = [] # This will hold regions for the currently displayed page (filtered or unfiltered)
        self.layout_processor = None # Initialize processor to None
        self.processing_thread = None
        
        self.setup_ui()
        # Initial display setup
        self.update_display()
        
    def setup_ui(self):
        # Create main frames
        self.control_frame = ttk.Frame(self.root)
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        self.display_frame = ttk.Frame(self.root)
        self.display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # File type selection
        self.file_type_frame = ttk.LabelFrame(self.control_frame, text="Select File Type")
        self.file_type_frame.pack(pady=5, fill=tk.X)
        
        self.file_type = tk.StringVar(value="both")
        ttk.Radiobutton(self.file_type_frame, text="PDF Files", variable=self.file_type, 
                       value="pdf").pack(anchor=tk.W, padx=5)
        ttk.Radiobutton(self.file_type_frame, text="Image Files", variable=self.file_type, 
                       value="image").pack(anchor=tk.W, padx=5)
        ttk.Radiobutton(self.file_type_frame, text="Both", variable=self.file_type, 
                       value="both").pack(anchor=tk.W, padx=5)
        
        # Control buttons
        ttk.Button(self.control_frame, text="Upload Files", command=self.upload_files).pack(pady=5)
        ttk.Button(self.control_frame, text="Previous Page", command=self.previous_page).pack(pady=5)
        ttk.Button(self.control_frame, text="Next Page", command=self.next_page).pack(pady=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.control_frame, variable=self.progress_var, 
                                          maximum=100)
        self.progress_bar.pack(pady=5, fill=tk.X)
        
        # Status label
        self.status_label = ttk.Label(self.control_frame, text="Ready")
        self.status_label.pack(pady=5)
        
        # Page navigation
        self.page_label = ttk.Label(self.control_frame, text="Page: 0/0")
        self.page_label.pack(pady=5)
        
        # Filter frame
        filter_frame = ttk.LabelFrame(self.control_frame, text="Filters")
        filter_frame.pack(pady=5, fill=tk.X)
        
        # Region type filter
        ttk.Label(filter_frame, text="Region Type:").pack(pady=2)
        self.region_filter = ttk.Combobox(filter_frame, 
                                        values=["All", "Text", "Table", "Figure", "Map", "Image", "Caption"])
        self.region_filter.set("All")
        self.region_filter.pack(pady=2)
        
        # Caption type filter
        ttk.Label(filter_frame, text="Caption Type:").pack(pady=2)
        self.caption_filter = ttk.Combobox(filter_frame,
                                         values=["All", "Figure", "Table", "Map"])
        self.caption_filter.set("All")
        self.caption_filter.pack(pady=2)
        
        # Apply filters button
        ttk.Button(filter_frame, text="Apply Filters", command=self.apply_filters).pack(pady=5)
        
        # Results display
        results_frame = ttk.LabelFrame(self.control_frame, text="Results")
        results_frame.pack(pady=5, fill=tk.BOTH, expand=True)
        
        # Add tabs for different views
        self.results_notebook = ttk.Notebook(results_frame)
        self.results_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Regions tab
        self.regions_text = ScrolledText(self.results_notebook, width=40, height=20)
        self.results_notebook.add(self.regions_text, text="Regions")
        
        # Captions tab
        self.captions_text = ScrolledText(self.results_notebook, width=40, height=20)
        self.results_notebook.add(self.captions_text, text="Captions")
        
        # Matplotlib figure for visualization
        self.fig, self.ax = plt.subplots(figsize=(10, 10))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.display_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def update_results_text(self):
        # Update regions text
        self.regions_text.delete(1.0, tk.END)
        for region in self.regions:
            self.regions_text.insert(tk.END, f"Region #{region['number']}\n")
            self.regions_text.insert(tk.END, f"Label: {region['label']}\n")
            self.regions_text.insert(tk.END, f"Position: {region['position']}\n")
            self.regions_text.insert(tk.END, f"BBox: {region['bbox']}\n")
            self.regions_text.insert(tk.END, f"Type: {region['region_type']}\n")
            if 'caption' in region:
                self.regions_text.insert(tk.END, f"Caption: {region['caption']}\n")
                self.regions_text.insert(tk.END, f"Caption Type: {region['caption_type']}\n")
            self.regions_text.insert(tk.END, f"Timestamp: {region['timestamp']}\n")
            self.regions_text.insert(tk.END, "-" * 40 + "\n")
        
        # Update captions text
        self.captions_text.delete(1.0, tk.END)
        captions = [r for r in self.regions if 'caption' in r]
        if captions:
            for region in captions:
                self.captions_text.insert(tk.END, f"Caption for Region #{region['number']}\n")
                self.captions_text.insert(tk.END, f"Text: {region['caption']}\n")
                self.captions_text.insert(tk.END, f"Type: {region['caption_type']}\n")
                self.captions_text.insert(tk.END, f"Associated Region Type: {region['region_type']}\n")
                self.captions_text.insert(tk.END, f"Position: {region['position']}\n")
                self.captions_text.insert(tk.END, "-" * 40 + "\n")
        else:
            self.captions_text.insert(tk.END, "No captions found in current page.\n")
    
    def apply_filters(self):
        logger.info("Applying filters...")
        region_type_filter = self.region_filter.get().lower()
        caption_type_filter = self.caption_filter.get().lower()
        
        # Get the original regions for the current page from the processor instance
        # Filter the regions list based on selected criteria
        current_page_regions_all = []
        if self.layout_processor and hasattr(self.layout_processor, 'regions_by_page') and 0 <= self.current_page < len(self.layout_processor.regions_by_page):
             # Get regions for the current page stored in the processor
            current_page_regions_all = self.layout_processor.regions_by_page[self.current_page]
            
            filtered_regions = current_page_regions_all

            if region_type_filter != "all":
                # Special handling for 'Caption' region type filter
                if region_type_filter == "caption":
                    filtered_regions = [r for r in filtered_regions if 'caption' in r]
                else:
                    filtered_regions = [r for r in filtered_regions if r.get('label', '').lower() == region_type_filter]

            if caption_type_filter != "all":
                filtered_regions = [r for r in filtered_regions 
                                  if 'caption_type' in r and r['caption_type'].lower() == caption_type_filter]
            
            self.regions = filtered_regions # Update the GUI's regions list with filtered results
            logger.info(f"Applied filters. Showing {len(self.regions)} regions.")
            self.update_display(apply_filter=True) # Update display without reprocessing

        else:
             # If processor or regions_by_page is not available, just update display with current data
            self.regions = [] # Clear regions if data is not ready
            logger.warning("Processor or regions_by_page not available during filter application.")
            self.update_display()

    
    def update_display(self, apply_filter=False):
        logger.info(f"Updating display for page {self.current_page + 1}, apply_filter={apply_filter}")
        if not self.images or not self.layout_processor or not hasattr(self.layout_processor, 'regions_by_page') or self.current_page >= len(self.layout_processor.regions_by_page):
            # Clear display if no images or data are loaded/available
            self.ax.clear()
            self.ax.set_title("Load files to begin")
            self.ax.axis('off')
            self.canvas.draw()
            self.page_label.config(text="Page: 0/0")
            self.regions_text.delete(1.0, tk.END)
            self.captions_text.delete(1.0, tk.END)
            self.status_label.config(text="Ready") # Reset status
            logger.info("Display cleared: No images or processed data available.")
            return
            
        # Clear the figure
        self.ax.clear()
        
        current_page_regions = []
        current_image = self.images[self.current_page]
        labeled_image = current_image # Default to original image

        try:
            # Get regions for the current page
            if apply_filter:
                 # Use the already filtered regions if apply_filter is True
                 current_page_regions = self.regions
                 logger.info(f"Displaying filtered regions: {len(current_page_regions)}")
                 # Draw labels on the original image using the filtered regions
                 labeled_image = self.layout_processor.draw_region_labels(Image.fromarray(np.array(current_image)), current_page_regions)

            else:
                # Get regions for the current page stored in the processor
                current_page_regions = self.layout_processor.regions_by_page[self.current_page]
                self.regions = current_page_regions # Update GUI's regions list with unfiltered regions for this page
                logger.info(f"Displaying unfiltered regions for page {self.current_page}: {len(current_page_regions)}")
                 # Draw labels on the original image using the regions from the processor
                labeled_image = self.layout_processor.draw_region_labels(Image.fromarray(np.array(current_image)), current_page_regions)

            # Save the labeled image
            labeled_image_path = self.layout_processor.base_output_dir / 'labeled_images'
            labeled_image_path.mkdir(exist_ok=True)
            labeled_image.save(labeled_image_path / f"labeled_image_page_{self.current_page + 1}.png")
            logger.info(f"Saved labeled image for page {self.current_page + 1} to {labeled_image_path}")

            # Save page-specific metadata
            page_metadata = {
                'page_number': self.current_page + 1,
                'total_regions': len(current_page_regions),
                'regions': current_page_regions,
                'timestamp': datetime.now().isoformat()
            }
            
            # Save in both metadata and json_output directories
            metadata_path = self.layout_processor.base_output_dir / 'metadata' / f'page_{self.current_page + 1}_metadata.json'
            json_output_path = self.layout_processor.base_output_dir / 'json_output' / f'page_{self.current_page + 1}_metadata.json'
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(page_metadata, f, indent=4)
            with open(json_output_path, 'w', encoding='utf-8') as f:
                json.dump(page_metadata, f, indent=4)
            
            logger.info(f"Saved page metadata to {metadata_path} and {json_output_path}")

            # Display labeled image
            self.ax.imshow(labeled_image)
            self.ax.axis('off')
            
            # Add title with page number and potentially statistics
            page_title = f"Page {self.current_page + 1} of {len(self.images)}"
            
            # Safely access statistics from the processor instance
            if hasattr(self.layout_processor, 'statistics') and self.layout_processor.statistics:
                stats = self.layout_processor.statistics
                page_title += f" | Total Regions: {stats.get('total_regions', 'N/A')}"
                
                regions_by_type = stats.get('regions_by_type', {})
                # Safely format regions by type statistics
                region_stats_str = ", ".join([f"{k.capitalize()}: {v}" for k, v in regions_by_type.items() if v is not None])
                if region_stats_str:
                     page_title += f" ({region_stats_str})"

                captions_by_type = stats.get('captions_by_type', {})
                # Safely format captions by type statistics
                caption_stats_str = ", ".join([f"{k.capitalize()}: {v}" for k, v in captions_by_type.items() if v is not None])
                if caption_stats_str:
                     page_title += f" | Captions: {caption_stats_str}"

            self.ax.set_title(page_title)
            
            # Add legend for region types and captions
            legend_elements = [
                patches.Patch(facecolor='none', edgecolor='red', label='Region'),
                patches.Patch(facecolor='none', edgecolor='blue', label='Caption')
            ]
            # Safely add legend to the plot
            try:
                self.ax.legend(handles=legend_elements, loc='upper right')
            except Exception as legend_e:
                 logger.warning(f"Could not add legend: {legend_e}") # Log warning instead of crashing

            self.canvas.draw()
            
            # Update page label
            self.page_label.config(text=f"Page: {self.current_page + 1}/{len(self.images)}")
            
            # Update results text if not applying filters (to show current page's full regions)
            if not apply_filter:
                 self.update_results_text() # This uses the unfiltered self.regions for the current page
            else:
                 # If filtering, update text display with filtered regions
                 self.update_results_text_filtered() # This uses the filtered self.regions

        except Exception as e:
            logger.error(f"Error processing page for display: {str(e)}")
            # Log the traceback for debugging
            logger.error(traceback.format_exc())
            messagebox.showerror("Error", f"Error processing page for display: {str(e)}")

    # Method to update results text based on the currently unfiltered regions for the page
    def update_results_text(self):
        logger.info(f"Updating results text for page {self.current_page + 1}")
        self.regions_text.delete(1.0, tk.END)
        self.captions_text.delete(1.0, tk.END)

        # Use the unfiltered regions for the current page from the processor instance if available
        current_page_unfiltered_regions = []
        if self.layout_processor and hasattr(self.layout_processor, 'regions_by_page') and 0 <= self.current_page < len(self.layout_processor.regions_by_page):
             current_page_unfiltered_regions = self.layout_processor.regions_by_page[self.current_page]
             logger.info(f"Found {len(current_page_unfiltered_regions)} unfiltered regions for text display.")

        filtered_captions = [r for r in current_page_unfiltered_regions if 'caption' in r]

        if not current_page_unfiltered_regions:
             self.regions_text.insert(tk.END, "No regions found for the current page.\n")
        else:
            for region in current_page_unfiltered_regions:
                 # Safely access region attributes
                 self.regions_text.insert(tk.END, f"Region #{region.get('number', 'N/A')}\n")
                 self.regions_text.insert(tk.END, f"Label: {region.get('label', 'N/A')}\n")
                 self.regions_text.insert(tk.END, f"Type: {region.get('region_type', 'N/A')}\n")
                 self.regions_text.insert(tk.END, f"Position: {region.get('position', 'N/A')}\n")
                 self.regions_text.insert(tk.END, f"BBox: {region.get('bbox', 'N/A')}\n")
                 if 'caption' in region:
                     self.regions_text.insert(tk.END, f"Caption: {region.get('caption', 'N/A')}\n")
                     self.regions_text.insert(tk.END, f"Caption Type: {region.get('caption_type', 'N/A')}\n")
                     self.regions_text.insert(tk.END, f"Caption Valid: {region.get('caption_valid', 'N/A')}\n")
                 self.regions_text.insert(tk.END, f"Timestamp: {region.get('timestamp', 'N/A')}\n")
                 self.regions_text.insert(tk.END, "-" * 40 + "\n")

        if not filtered_captions:
            self.captions_text.insert(tk.END, "No captions found for the current page.\n")
        else:
            for region in filtered_captions:
                # Safely access region attributes for captions
                self.captions_text.insert(tk.END, f"Caption for Region #{region.get('number', 'N/A')}\n")
                self.captions_text.insert(tk.END, f"Text: {region.get('caption', 'N/A')}\n")
                self.captions_text.insert(tk.END, f"Type: {region.get('caption_type', 'N/A')}\n")
                self.captions_text.insert(tk.END, f"Associated Region Type: {region.get('region_type', 'N/A')}\n")
                self.captions_text.insert(tk.END, f"Position: {region.get('position', 'N/A')}\n")
                self.captions_text.insert(tk.END, "-" * 40 + "\n")


    # New method to update results text based on the currently filtered regions
    def update_results_text_filtered(self):
        logger.info("Updating results text based on filtered regions.")
        self.regions_text.delete(1.0, tk.END)
        self.captions_text.delete(1.0, tk.END)

        filtered_captions = [r for r in self.regions if 'caption' in r]

        if not self.regions:
             self.regions_text.insert(tk.END, "No regions match the current filters.\n")
        else:
            for region in self.regions:
                 # Safely access region attributes
                 self.regions_text.insert(tk.END, f"Region #{region.get('number', 'N/A')}\n")
                 self.regions_text.insert(tk.END, f"Label: {region.get('label', 'N/A')}\n")
                 self.regions_text.insert(tk.END, f"Type: {region.get('region_type', 'N/A')}\n")
                 self.regions_text.insert(tk.END, f"Position: {region.get('position', 'N/A')}\n")
                 self.regions_text.insert(tk.END, f"BBox: {region.get('bbox', 'N/A')}\n")
                 if 'caption' in region:
                     self.regions_text.insert(tk.END, f"Caption: {region.get('caption', 'N/A')}\n")
                     self.regions_text.insert(tk.END, f"Caption Type: {region.get('caption_type', 'N/A')}\n")
                     self.regions_text.insert(tk.END, f"Caption Valid: {region.get('caption_valid', 'N/A')}\n")
                 self.regions_text.insert(tk.END, f"Timestamp: {region.get('timestamp', 'N/A')}\n")
                 self.regions_text.insert(tk.END, "-" * 40 + "\n")

        if not filtered_captions:
            self.captions_text.insert(tk.END, "No captions match the current filters.\n")
        else:
            for region in filtered_captions:
                # Safely access region attributes for captions
                self.captions_text.insert(tk.END, f"Caption for Region #{region.get('number', 'N/A')}\n")
                self.captions_text.insert(tk.END, f"Text: {region.get('caption', 'N/A')}\n")
                self.captions_text.insert(tk.END, f"Type: {region.get('caption_type', 'N/A')}\n")
                self.captions_text.insert(tk.END, f"Associated Region Type: {region.get('region_type', 'N/A')}\n")
                self.captions_text.insert(tk.END, f"Position: {region.get('position', 'N/A')}\n")
                self.captions_text.insert(tk.END, "-" * 40 + "\n")

    def upload_files(self):
        logger.info("Upload files button clicked.")
        file_type = self.file_type.get()
        filetypes = []
        
        if file_type in ["pdf", "both"]:
            filetypes.append(("PDF files", "*.pdf"))
        if file_type in ["image", "both"]:
            filetypes.append(("Image files", "*.png *.jpg *.jpeg"))
            
        file_paths = filedialog.askopenfilenames(filetypes=filetypes)
        if file_paths:
            logger.info(f"Selected files: {file_paths}")
            self.status_label.config(text="Processing files...")
            self.progress_var.set(0)

            # Re-initialize layout_processor for a new batch of files
            self.layout_processor = LayoutProcessor()
            self.regions = [] # Clear previous regions
            self.images = [] # Clear previous images
            self.current_page = 0 # Reset page number
            self.update_display() # Clear display
            
            # Process files in a separate thread
            self.processing_thread = threading.Thread(
                target=self.process_files_thread,
                args=(file_paths,)
            )
            self.processing_thread.start()
            
    def process_files_thread(self, file_paths):
        logger.info("Processing files in background thread.")
        try:
            # Create output directories if they don't exist
            output_base = Path(__file__).parent.absolute() / 'output_regions'
            output_base.mkdir(exist_ok=True)
            
            # Initialize processor with the correct base output directory
            self.layout_processor = LayoutProcessor()
            self.layout_processor.base_output_dir = output_base
            
            # Create all necessary subdirectories
            for dir_name in ['images', 'text', 'tables', 'figures', 'maps', 'captions', 'metadata', 'json_output', 'labeled_images']:
                (output_base / dir_name).mkdir(exist_ok=True)
            
            logger.info(f"Created output directories in: {output_base}")
            
            # Process files
            logger.info("Calling process_files from layout_model...")
            self.images, self.layout_processor = process_files(file_paths, processor=self.layout_processor)
            
            logger.info("File processing complete.")
            logger.info(f"Loaded {len(self.images)} images.")
            
            if self.layout_processor and hasattr(self.layout_processor, 'regions_by_page'):
                total_processed_regions = sum(len(page_regions) for page_regions in self.layout_processor.regions_by_page)
                logger.info(f"Total regions processed across all pages: {total_processed_regions}")
                
                # Save overall metadata
                metadata = {
                    'total_pages': len(self.images),
                    'total_regions': total_processed_regions,
                    'regions_by_page': [len(regions) for regions in self.layout_processor.regions_by_page],
                    'statistics': self.layout_processor.statistics,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Save metadata in both locations
                metadata_path = output_base / 'metadata' / 'overall_metadata.json'
                json_output_path = output_base / 'json_output' / 'overall_metadata.json'
                
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=4)
                with open(json_output_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=4)
                
                logger.info(f"Saved overall metadata to {metadata_path} and {json_output_path}")
            
            self.current_page = 0
            self.root.after(0, self.update_display) # Update display on the main thread
            self.root.after(0, lambda: self.status_label.config(text="Ready"))
            self.root.after(0, lambda: self.progress_var.set(100))
            
        except Exception as e:
            logger.error(f"Error processing files in background thread: {str(e)}")
            logger.error(traceback.format_exc())
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error processing files: {str(e)}"))
            self.root.after(0, lambda: self.status_label.config(text="Error processing files"))

    def previous_page(self):
        logger.info(f"Previous page button clicked. Current page: {self.current_page}")
        if self.current_page > 0:
            self.current_page -= 1
            self.update_display()
        else:
             logger.info("Already on the first page.")
            
    def next_page(self):
        logger.info(f"Next page button clicked. Current page: {self.current_page}, Total images: {len(self.images)}")
        if self.current_page < len(self.images) - 1:
            self.current_page += 1
            self.update_display()
        else:
             logger.info("Already on the last page.")

if __name__ == "__main__":
    root = tk.Tk()
    app = LayoutAnalyzerGUI(root)
    root.mainloop() 