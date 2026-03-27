# Plan: Professional Quarto Portfolio Conversion

This plan outlines the steps to convert the current folder structure into a professional, organized, and easily maintainable Quarto portfolio.

## 1. Project Infrastructure
- [x] **Create `_quarto.yml`**: Define the global configuration, including the website navbar, theme, and custom CSS.
- [x] **Establish Directory Structure**: Organize content into logical folders (e.g., `projects/`, `about/`, `assets/`).
- [x] **Setup Version Control**: Ensure `.gitignore` is properly configured for a Quarto project (ignoring `_site/`, `*_files/`, etc.).

## 2. Content Conversion
- [x] **Home Page (`index.qmd`)**: Convert the existing `index.html` content into a Quarto Markdown file using the `solana` about page template.
- [x] **About Page (`about.qmd`)**: Reconstruct the `about.html` content into a clean `.qmd` file.
- [x] **Project Showcase**:
    - [x] Convert `SP500-Portfolio.ipynb` (or its output) into a dedicated page within a `projects/` directory.
    - [x] Implement a **Project Listing** page with a **Grid layout** (using cards and thumbnails) to dynamically display your work.

## 3. Design & Aesthetics
- [x] **Custom Theme Definition**: Create a `custom.scss` file that inherits from the `superhero` theme but overrides:
    - Background color to a darker blue (e.g., `#0a192f` or similar).
    - Navigation bar background to white.
    - Button and link hover effects to match the glow/shadow in the current `styles.css`.
- [x] **Refine `styles.css`**: Migrate the 8px-rule spacing and interactive feedback logic into the SCSS framework.
- [x] **Responsive Design**: Ensure the layout (especially the horizontal hero) works seamlessly on mobile devices.

## 4. Features & Enhancements
- [x] **Search & Navigation**: Enable site-wide search and a structured navigation menu.
- [x] **Social Integration**: Add links to LinkedIn, GitHub, and email in the header/footer.
- [x] **SEO & Metadata**: Configure `robots.txt`, `sitemap.xml`, and page-specific metadata for better search engine visibility.

## 5. Deployment & Maintenance
- [x] **Build Pipeline**: Test the full site build using `quarto render`.
- [ ] **Deployment Strategy**: Set up GitHub Pages or another hosting provider.
- [ ] **Documentation**: Create a small README on how to add new projects.

## 6. Notebook Integration
- [x] **Direct Rendering**: Move or link `SP500-Portfolio.ipynb` into the `projects/` folder.
- [x] **Metadata Injection**: Add Quarto YAML metadata (title, categories, image) directly to the notebook's first cell.
- [x] **Path Correction**: Ensure the notebook can still access data in `Projects/SP500_Portfolio/data/` from its new location.
- [x] **Listing Update**: Ensure the project grid dynamically picks up the notebook.

---

### Questions for the User
*I will ask these one by one to ensure we stay aligned.*

1. **DONE**: Theme Preference (Superhero base with darker blue bg and white navbar, buttons and links light up when you hover over them excep in the navigation bar).
2. **DONE**: Project Listing (Grid layout with cards).
3. **DONE**: Navigation Menu (Home, Projects, About).
4. **DONE**: Social Links Placement (Header).
5. **DONE**: Specific Social Profiles (LinkedIn, GitHub, Email).

---
*Plan finalized. Ready to begin implementation of Phase 1.*
