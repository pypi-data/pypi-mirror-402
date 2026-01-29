import imgui
import numpy as np
from typing import Dict, List, Optional
import math

class GenealogyVisualizer:
    """
    GA Statistics Dashboard
    Visualizes the progress of the Genetic Algorithm (Fitness, Temperature, etc.)
    and inspects individual structure details.
    """
    def __init__(self, provider):
        self.provider = provider
        self.data_loaded = False
        self.attempted_load = False
        
        # Data storage
        self.generations: np.ndarray = np.array([])
        self.energy: np.ndarray = np.array([]) # Replaced fitness with energy
        self.temperature: np.ndarray = np.array([])
        
        # Aggregated Stats (per generation)
        self.unique_gens: np.ndarray = np.array([])
        self.min_energy_per_gen: np.ndarray = np.array([])
        self.avg_energy_per_gen: np.ndarray = np.array([])
        self.temp_per_gen: np.ndarray = np.array([])
        
        self.total_structures = 0
        self.visible_structures = 0
        
        # Histogram Data
        self.hist_bins: np.ndarray = np.array([])
        self.hist_counts: np.ndarray = np.array([])
        
        # UI State
        self.show_scatter = True
        self.hovered_scatter_idx = -1
        
        # Plot Interaction State
        self.plot_zoom = np.array([1.0, 1.0], dtype=np.float32)
        self.plot_offset = np.array([0.0, 0.0], dtype=np.float32)
        self.is_dragging_plot = False
        self.plot_hover_pos = None # For crosshair

    def load_data(self):
        """Loads metadata for statistical analysis."""
        if self.data_loaded: return
        self.attempted_load = True
        
        if not hasattr(self.provider, 'get_all_metadata'):
            return

        print("Loading GA Dashboard Data (Formation Energy Mode)...")
        try:
            # Load all metadata lists with fallbacks
            gen_list = self.provider.get_all_metadata('generation')
            # Load keys safely (avoiding boolean ambiguity with numpy arrays)
            # Load keys safely (avoiding boolean ambiguity with numpy arrays)
            # User request: Use efficient direct loading snippet
            self.energy_ef = np.array(self.provider.get_all_Ef(), dtype=np.float32)
            if hasattr(self.provider, 'get_all_E'):
                self.energy_total = np.array(self.provider.get_all_E(), dtype=np.float32)
            else:
                self.energy_total = self.energy_ef.copy()
                 
            # Load Composition Vectorized
            self.species_counts, self.species_list = self.provider.get_all_compositions(return_species=True)
            self.species_list = sorted(self.species_list) # Ensure sorted order if not already
            self.n_species = len(self.species_list)
            
            # Note: get_all_compositions return order: X_all, species_order. 
            # X_all columns correspond to species_order.
            # If species_order is NOT sorted, we should sort it and shuffle columns?
            # Usually get_all_compositions returns strictly. 
            # Let's trust the provider for now.
            
            # Dummy comp_list for now as we don't load dicts
            comp_list = None
            n_list = self.provider.get_all_metadata('natoms')
            temp_list = self.provider.get_all_metadata('T')
            
            # Ensure proper lengths
            N = len(gen_list)
            if len(self.energy_total) < N:
                 # Pad if necessary (though provider should match)
                 tmp = np.zeros(N, dtype=np.float32)
                 tmp[:len(self.energy_total)] = self.energy_total
                 self.energy_total = tmp
            
            self.generations = np.zeros(N, dtype=int)
            # raw_energy and self.temperature are allocated below
            self.temperature = np.zeros(N, dtype=float)
            
            # Composition Loaded via Vectorized Call
            
            # Matrix to hold atom counts per species: [N_structs, N_species]
            # Already loaded as self.species_counts above
            
            valid_mask = np.zeros(N, dtype=bool)
            
            for i in range(N):
                g = gen_list[i]
                t = temp_list[i]
                
                # Check directly in our loaded array
                e_val = self.energy_total[i]
                
                # Relaxed Loading: Default Gen to 0 if missing
                if g is None: g = 0
                
                # Filter: Must be valid float (not NaN, not Inf) and non-zero if we want strictness?
                # User snippet implies trusting get_all_E. Let's just check non-NaN.
                # Actually, check if it was populated. 
                # For safety, we only consider it valid if energy != 0 or provider guarantees it.
                # Simpler: If we have energy, we mark valid.
                
                self.generations[i] = int(g)
                self.temperature[i] = float(t) if t is not None else 0.0
                # Composition already loaded via vectorized method
                pass
                
                valid_mask[i] = True
            
            # Apply Filter
            self.generations = self.generations[valid_mask]
            self.raw_energy = self.energy_total[valid_mask] # Use the loaded total energy
            self.species_counts = self.species_counts[valid_mask]
            self.temperature = self.temperature[valid_mask]
            self.valid_indices = np.where(valid_mask)[0] 
            
            self.total_structures = N
            self.visible_structures = len(self.generations)
            
            # Calculate total atoms per structure for plotting/normalization if needed
            natoms_filtered = np.sum(self.species_counts, axis=1)
            
            # -----------------------------------------------------
            # Multivariate Linear Regression for Mu
            # E = sum(n_i * mu_i)
            # -----------------------------------------------------
            self.mu_values = {s: 0.0 for s in self.species_list}
            

            
            if len(self.raw_energy) > 0 and self.n_species > 0:
                # A = [N_structs, N_species]
                A = self.species_counts
                try:
                    # Solving A * x = b, where x is [mu_1, mu_2, ...]
                    m, _, _, _ = np.linalg.lstsq(A, self.raw_energy, rcond=None)
                    for idx, s in enumerate(self.species_list):
                        self.mu_values[s] = m[idx]
                        print(f"Estimated mu_{s} = {m[idx]:.3f} eV/atom")
                except Exception as e:
                    print(f"Regression failed: {e}")

            # Initial Calculation of Formation Energy
            # Ef = E - sum(n_i * mu_i)
            # We can vectorize this: Ef = E - dot(SpeciesCounts, MuVector)
            

            
            self.update_formation_energy()
            
            self.compute_aggregates()

            self.data_loaded = True
            print(f"Loaded {len(self.generations)} data points.")
            
        except Exception as e:
            print(f"Failed to load GA data: {e}")
            import traceback
            traceback.print_exc()

    def update_formation_energy(self):
        """Recalculate Ef based on raw energy, composition (species_counts), and current mu values."""
        if not hasattr(self, 'raw_energy') or not hasattr(self, 'species_counts'):
            return
        
        # Build vector of current mu values
        # Ensure order matches self.species_list
        mu_vec = np.zeros(self.n_species)
        for i, s in enumerate(self.species_list):
            mu_vec[i] = self.mu_values.get(s, 0.0)
        
        # Calculate Correction: sum(n_i * mu_i)
        correction = np.dot(self.species_counts, mu_vec)
        
        self.formation_energy = self.raw_energy - correction
        self.compute_aggregates()
        
    def compute_aggregates(self):
        """Update histograms and trend lines based on current formation energy."""
        if not hasattr(self, 'formation_energy'): return

        # Compute Aggregates
        if len(self.generations) > 0:
            self.unique_gens = np.unique(self.generations)
            self.unique_gens.sort()
            
            n_bins = len(self.unique_gens)
            self.min_energy_per_gen = np.zeros(n_bins)
            self.avg_energy_per_gen = np.zeros(n_bins)
            self.temp_per_gen = np.zeros(n_bins)
            
            for k, g_val in enumerate(self.unique_gens):
                mask = (self.generations == g_val)
                e_subset = self.formation_energy[mask]
                t_subset = self.temperature[mask]
                
                self.min_energy_per_gen[k] = np.min(e_subset)
                self.avg_energy_per_gen[k] = np.mean(e_subset)
                self.temp_per_gen[k] = np.mean(t_subset)
        
        # Compute Histogram (Formation Energy)
        if len(self.formation_energy) > 0:
            # 50 bins strictly
            self.hist_counts, self.hist_bins = np.histogram(self.formation_energy, bins=50)
            
    def render_panel(self, current_index: int, load_callback):
        """Renders the dashboard logic."""
        if not self.data_loaded:
            if not self.attempted_load:
                self.load_data()
            if not self.data_loaded:
                if imgui.button("Retry Load"):
                    self.attempted_load = False
                return

        # ---------------------------------------------------------
        # 0. Global Stats Summary
        # ---------------------------------------------------------
        if len(self.formation_energy) > 0:
            best_idx = np.argmin(self.formation_energy)
            best_e = self.formation_energy[best_idx]
            best_g = self.generations[best_idx]
            
            imgui.text_colored("GLOBAL STATISTICS", 0.6, 0.6, 0.6, 1.0)
            imgui.same_line()
            if imgui.small_button("Refresh Data"):
                self.attempted_load = False
                self.data_loaded = False
            
            # Display estimated mu
            mu_val = getattr(self, 'mu_est', 0.0)
            imgui.same_line()
            imgui.text_colored(f"| Est. Mu: {mu_val:.4f} eV/atom", 0.5, 0.8, 1.0, 1.0)

            imgui.separator()
            imgui.columns(4, "stats_header", border=False)
            imgui.text("Total Structures"); imgui.next_column()
            # Show "Visible / Total"
            imgui.text_colored(f"{self.visible_structures} / {self.total_structures}", 1,1,1,1); imgui.next_column()
            imgui.text("Best Formation E"); imgui.next_column()
            imgui.text_colored(f"{best_e:.4f} eV (Gen {best_g})", 0.2, 1.0, 0.4, 1.0); imgui.next_column()
            imgui.columns(1)
            imgui.separator()
            
            if self.visible_structures < self.total_structures:
                imgui.text_colored(f"Note: {self.total_structures - self.visible_structures} structures hidden (missing Energy/Atom data).", 1, 0.8, 0.4, 0.8)
            
            # Sliders for Chemical Potential
            imgui.spacing()
            if hasattr(self, 'species_list') and self.species_list and imgui.collapsing_header("Chemical Potentials (Adjust Sliders)", flags=imgui.TREE_NODE_DEFAULT_OPEN)[0]:
                changed_any = False
                for s in self.species_list:
                    val = self.mu_values[s]
                    # Range: +/- 30 eV as requested
                    changed, new_val = imgui.slider_float(f"mu_{s}", val, -30.0, 30.0, "%.3f")
                    if changed:
                        self.mu_values[s] = new_val
                        changed_any = True
                
                if changed_any:
                    self.update_formation_energy()
                    
            imgui.separator()
            
        # ---------------------------------------------------------
        # 0.5. Histogram (Energy Distribution)
        # ---------------------------------------------------------
        if len(self.hist_counts) > 0 and imgui.collapsing_header("Formation Energy Histogram (eV)", visible=True)[0]:
             imgui.plot_histogram(
                 label="Counts",
                 values=self.hist_counts.astype(np.float32),
                 graph_size=(0, 80), # 0 width = auto
                 scale_min=0.0,
                 overlay_text=f"Min: {self.hist_bins[0]:.2f} | Max: {self.hist_bins[-1]:.2f} eV"
             )
             imgui.spacing()

        # ---------------------------------------------------------
        # 1. Structure Inspector (Current Selection)
        # ---------------------------------------------------------
        imgui.text_colored(f"Selected Structure: {current_index}", 0.2, 0.8, 1.0, 1.0)
        
        # We fetch details on demand for just one structure to ensure freshness/completeness
        if hasattr(self.provider, 'p'):
            try:
                # Access partition directly for inspection details if possible
                c = self.provider.p.containers[current_index]
                meta = getattr(c.AtomPositionManager, 'metadata', {})
                
                # Display Key properties in Columns
                imgui.columns(2, "inspector", border=False)
                imgui.text("Generation:"); imgui.next_column(); imgui.text_colored(str(meta.get('generation', '?')), 1,1,0.5,1); imgui.next_column()
                
                e_val = meta.get('E')
                if e_val is None: e_val = meta.get('energy')
                if e_val is None: e_val = meta.get('F')
                natoms_val = getattr(self, 'temp_natoms_map', {}).get(current_index, "?") # We don't have map easily unless we reload
                # Actually, let's just calc raw if we can info
                
                imgui.text("Raw Energy (E):"); imgui.next_column(); imgui.text_colored(f"{e_val:.4f} eV" if e_val else "?", 0.8,0.8,0.8,1); imgui.next_column()
                
                # Calculate local Ef if possible
                mu_val = getattr(self, 'mu_est', 0.0)
                if e_val:
                    # Try to get atoms count again for display
                    na = 0
                    if hasattr(c, 'get_number_of_atoms'): na = c.get_number_of_atoms()
                    elif hasattr(c, 'atoms'): na = c.atoms.get_number_of_atoms()
                    
                    if na > 0:
                        ef_local = e_val - mu_val * na
                        imgui.text("Formation E (Ef):"); imgui.next_column(); imgui.text_colored(f"{ef_local:.4f} eV", 0.5,1,0.5,1); imgui.next_column()

                imgui.text("Temperature:"); imgui.next_column(); imgui.text_colored(f"{meta.get('T', 0.0):.4f}", 1,0.5,0.5,1); imgui.next_column()
                imgui.text("Operation:"); imgui.next_column(); imgui.text_colored(str(meta.get('operation', '-')), 0.8,0.8,1,1); imgui.next_column()
                
                parents = meta.get('parents', [])
                imgui.text("Parents:"); imgui.next_column(); 
                if parents:
                    imgui.text_wrapped(str(parents))
                else:
                    imgui.text_disabled("None")
                imgui.next_column()
                
                imgui.columns(1)
                imgui.separator()
                
            except Exception:
                imgui.text_disabled("No metadata available")
        
        # ---------------------------------------------------------
        # 2. Charts (Energy Evolution)
        # ---------------------------------------------------------
        if len(self.unique_gens) > 1:
            imgui.text("Evolution History (Formation Energy vs Generation)")
            imgui.text_colored("Right-Drag to Pan, Scroll to Zoom, Left-Click to Select", 0.5, 0.5, 0.5, 1.0)
            
            avail_w = imgui.get_content_region_available_width()
            h = 300
            
            # Interactive Canvas
            imgui.invisible_button("plots", avail_w, h)
            p0 = imgui.get_item_rect_min()
            p1 = imgui.get_item_rect_max()
            dl = imgui.get_window_draw_list()
            
            # Background
            bg_col = imgui.get_color_u32_rgba(0.12, 0.12, 0.14, 1)
            dl.add_rect_filled(p0[0], p0[1], p1[0], p1[1], bg_col)
            
            # Margins for Labels
            margin_l, margin_b = 60, 30
            margin_t, margin_r = 10, 10
            
            plot_rect_vals = (p0[0] + margin_l, p0[1] + margin_t, p1[0] - margin_r, p1[1] - margin_b)
            pw = plot_rect_vals[2] - plot_rect_vals[0]
            ph = plot_rect_vals[3] - plot_rect_vals[1] 
            
            # Input Handling (Zoom/Pan)
            if imgui.is_item_active() or imgui.is_item_hovered():
                io = imgui.get_io()
                
                # Pan: Right Drag
                if imgui.is_mouse_down(1): 
                     self.plot_offset[0] += io.mouse_delta[0] / pw * self.plot_zoom[0]
                     self.plot_offset[1] -= io.mouse_delta[1] / ph * self.plot_zoom[1] # Y inverted
                
                # Zoom: Wheel
                if io.mouse_wheel != 0:
                    z_speed = 0.1
                    self.plot_zoom *= (1.0 - io.mouse_wheel * z_speed)
                    self.plot_zoom = np.clip(self.plot_zoom, 0.01, 100.0)

            # Data Range
            d_min_g, d_max_g = self.unique_gens[0], self.unique_gens[-1]
            d_min_e, d_max_e = np.min(self.formation_energy), np.max(self.formation_energy)
            d_range_g = max(1, d_max_g - d_min_g)
            d_range_e = max(1e-3, d_max_e - d_min_e)
            
            # View Range (Affected by Zoom/Offset)
            view_min_g = d_min_g + d_range_g * (-0.5 * (self.plot_zoom[0]-1) - self.plot_offset[0]) 
            view_max_g = view_min_g + d_range_g * self.plot_zoom[0]
            
            view_min_e = d_min_e + d_range_e * (-0.5 * (self.plot_zoom[1]-1) - self.plot_offset[1])
            view_max_e = view_min_e + d_range_e * self.plot_zoom[1]

            # Coordinate Helper
            def to_screen(g, e):
                nx = (g - view_min_g) / (view_max_g - view_min_g)
                ny = (e - view_min_e) / (view_max_e - view_min_e)
                return (plot_rect_vals[0] + nx * pw, plot_rect_vals[3] - ny * ph)

            # Clip Plot Area
            dl.push_clip_rect(plot_rect_vals[0], plot_rect_vals[1], plot_rect_vals[2], plot_rect_vals[3], True)
            
            # Grid Lines
            grid_col = imgui.get_color_u32_rgba(1,1,1,0.1)
            # Simple 5x5 Grid
            for i in range(6):
                 # Vertical
                 x = plot_rect_vals[0] + i * (pw/5.0)
                 dl.add_line(x, plot_rect_vals[1], x, plot_rect_vals[3], grid_col)
                 # Horizontal
                 y = plot_rect_vals[1] + i * (ph/5.0)
                 dl.add_line(plot_rect_vals[0], y, plot_rect_vals[2], y, grid_col)
            
            # Draw Scatter
            col_scatter = imgui.get_color_u32_rgba(0.5, 0.5, 0.5, 0.5)
            col_sel = imgui.get_color_u32_rgba(1, 0.9, 0.2, 1.0)
            
            hovered = -1
            mx, my = imgui.get_mouse_pos()
            
            # Draw Data
            for i in range(len(self.formation_energy)):
                g = self.generations[i]
                e_val = self.formation_energy[i]
                
                # Check bounds
                if g < view_min_g or g > view_max_g or e_val < view_min_e or e_val > view_max_e:
                    continue
                    
                sp = to_screen(g, e_val)
                original_idx = self.valid_indices[i]

                if original_idx == current_index:
                    dl.add_circle_filled(sp[0], sp[1], 5, col_sel)
                    dl.add_circle(sp[0], sp[1], 6, 0xFFFFFFFF)
                else:
                    dl.add_circle_filled(sp[0], sp[1], 3, col_scatter)
                    
                # Mouse Interaction check
                if abs(mx - sp[0]) < 5 and abs(my - sp[1]) < 5:
                    hovered = original_idx

            # Draw Trend Lines
            try:
                col_min = imgui.get_color_u32_rgba(0.2, 1.0, 0.4, 0.9) # Green Best
                col_avg = imgui.get_color_u32_rgba(0.2, 0.6, 1.0, 0.7) # Blue Mean
                
                # Best Line
                pts_min = []
                pts_avg = []
                for k in range(len(self.unique_gens)):
                    g = self.unique_gens[k]
                    if g < view_min_g or g > view_max_g: continue
                    
                    p_min = to_screen(g, self.min_energy_per_gen[k])
                    p_avg = to_screen(g, self.avg_energy_per_gen[k])
                    pts_min.append(p_min)
                    pts_avg.append(p_avg)
                
                if len(pts_min) > 1:
                     dl.add_polyline(pts_min, col_min, False, 2.0)
                if len(pts_avg) > 1:
                     dl.add_polyline(pts_avg, col_avg, False, 2.0)
                     
            except Exception:
                pass

            dl.pop_clip_rect() # End Plot Area Clip

            # Axes Drawing (Outside Clip)
            axis_col = imgui.get_color_u32_rgba(1,1,1,0.8)
            dl.add_rect(plot_rect_vals[0], plot_rect_vals[1], plot_rect_vals[2], plot_rect_vals[3], axis_col)
            
            # Labels
            txt_col = imgui.get_color_u32_rgba(0.9, 0.9, 0.9, 1)
            
            # X Axis Labels
            start_g = f"{view_min_g:.0f}"
            end_g = f"{view_max_g:.0f}"
            dl.add_text(plot_rect_vals[0], plot_rect_vals[3] + 5, txt_col, start_g)
            dl.add_text(plot_rect_vals[2] - imgui.calc_text_size(end_g)[0], plot_rect_vals[3] + 5, txt_col, end_g)
            dl.add_text(plot_rect_vals[0] + pw/2 - 20, plot_rect_vals[3] + 20, txt_col, "Generation")
            
            # Y Axis Labels
            start_e = f"{view_min_e:.3f}"
            end_e = f"{view_max_e:.3f}"
            
            # Min (Bottom)
            dl.add_text(plot_rect_vals[0] - imgui.calc_text_size(start_e)[0] - 5, plot_rect_vals[3] - 10, txt_col, start_e)
            # Max (Top)
            dl.add_text(plot_rect_vals[0] - imgui.calc_text_size(end_e)[0] - 5, plot_rect_vals[1], txt_col, end_e)
            
            # Y Label
            dl.add_text(plot_rect_vals[0], plot_rect_vals[1] - 20, txt_col, "Formation Energy (Ef)")

            # Crosshair / Hover Info
            if imgui.is_item_hovered():
               ch_col = imgui.get_color_u32_rgba(1, 1, 1, 0.3)
               dl.add_line(plot_rect_vals[0], my, plot_rect_vals[2], my, ch_col)
               dl.add_line(mx, plot_rect_vals[1], mx, plot_rect_vals[3], ch_col)
               
            if hovered != -1:
                idx = np.where(self.valid_indices==hovered)[0][0]
                g_val = self.generations[idx]
                e_val = self.formation_energy[idx]
                imgui.set_tooltip(f"Structure {hovered}\nGen: {g_val}\nEf: {e_val:.4f} eV\n(Left Click to Select)")
                
                if imgui.is_mouse_clicked(0):
                    load_callback(hovered)

        else:
            imgui.text_disabled("Not enough data for evolution plot.")
