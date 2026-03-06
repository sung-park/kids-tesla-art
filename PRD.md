# Product Requirements Document (PRD): Kids Tesla Art

## 1. Project Overview
**Kids Tesla Art** is an open-source web application designed to transform children's hand-drawn, colored templates into custom wrap files for Tesla vehicles. Users can download a printable template, let their kids color it, upload a photo of the finished artwork, and automatically receive a formatted PNG file ready to be applied directly to their Tesla's in-car 3D model.

## 2. Target Audience
- Tesla owners with children who want a personalized, family-friendly in-car experience.
- Tesla enthusiasts looking for an automated, easy way to create custom wraps without needing professional design software (like Photoshop).

## 3. User Journey
1. **Download & Print:** User downloads a simplified, coloring-book-style Tesla template (PDF) equipped with predefined alignment markers.
2. **Coloring:** Children color the printed template using crayons, markers, or paints.
3. **Upload:** User captures a photo using their mobile device's camera or drags and drops a scanned image via the desktop web interface.
4. **Auto-Processing:** The backend detects the alignment markers, corrects the perspective, removes the white paper background (making it transparent), and maps the colored areas seamlessly onto the official Tesla UV wrap template.
5. **Download & Apply:** User receives an optimized PNG file (under 1MB, 1024x1024). The site provides clear instructions on how to transfer the file to the car using a USB drive.

## 4. Functional Requirements
- **F1. Template Generator:** Provide downloadable PDF templates for various Tesla models (Model 3, Model Y, Cybertruck, etc.) with ArUco/QR markers integrated into the corners for precise computer vision alignment.
- **F2. Cross-Platform Upload Interface:** - Mobile: Native camera integration for capturing images with a scanner-like guide UI.
  - Desktop: Drag-and-drop file upload zone.
- **F3. Image Processing Pipeline (Backend):**
  - Perspective warping and alignment using marker detection.
  - Background removal and alpha channel extraction to isolate the drawing.
  - Auto-mapping onto the official Tesla UV coordinates.
- **F4. File Optimization:** Compress the final output PNG to be strictly under 1MB and resize to the recommended 1024x1024 pixels, stripping out unsupported characters from the filename.
- **F5. Onboarding & Guide:** Provide a step-by-step visual guide on formatting a USB drive (exFAT/FAT32), creating the `Wraps` root folder, and applying the design via the Tesla Toybox.

## 5. Technical Architecture
- **Frontend:** React / Next.js with Tailwind CSS (Responsive, Mobile-First Web).
- **Backend:** Python (FastAPI), OpenCV (Image processing & alignment), `rembg` (Background removal), Pillow (Image manipulation & compression).
- **Infrastructure:** Designed to be containerized (Docker) and deployed on Oracle Cloud Infrastructure (OCI). Stateless architecture for minimal maintenance and easy open-source scaling.

## 6. Constraints & Limitations
- **USB Transfer Dependency:** Due to Tesla's system architecture, custom wrap files cannot be sent to the car via cloud or API. The physical transfer via USB drive is mandatory, making the UI's USB guide a critical component of the service.
