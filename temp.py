def update_placeholder(self, target_placeholder, new_value):
        """Scans all slides to find the placeholder and replaces it while preserving formatting."""
        if not self.prs:
            return

        new_value_str = str(new_value)
        found = False

        for slide in self.prs.slides:
            for shape in slide.shapes:
                if not shape.has_text_frame:
                    continue
                
                # Dig into the paragraph level to preserve Left/Right/Center alignment
                for paragraph in shape.text_frame.paragraphs:
                    
                    # 1. First, try to replace it at the "Run" level.
                    # This preserves exact font styling (colors, bold, size).
                    for run in paragraph.runs:
                        if target_placeholder in run.text:
                            run.text = run.text.replace(target_placeholder, new_value_str)
                            found = True
                            print(f"Success: Updated '{target_placeholder}' -> '{new_value_str}'")

                    # 2. Fallback: If PowerPoint split the placeholder across multiple hidden runs,
                    # replace it at the Paragraph level. This keeps alignment perfectly intact.
                    if not found and target_placeholder in paragraph.text:
                        paragraph.text = paragraph.text.replace(target_placeholder, new_value_str)
                        found = True
                        print(f"Success (Paragraph level): Updated '{target_placeholder}' -> '{new_value_str}'")

        if not found:
            print(f"Warning: Placeholder '{target_placeholder}' not found in the template.")
