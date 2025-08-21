# Jupyter Student Stack

Jupyter Student Stack is a Docker image designed for educational environments, providing a ready-to-use JupyterLab setup with multiple programming language kernels and useful extensions for teaching and learning.

## Features

- **Multi-language support:** Includes kernels for Python, Java, JavaScript, C, and SQL.
- **Pre-installed extensions:** nbgrader, nbgitpuller, resource usage monitor, variable inspector, and JupyterLab RISE for presentations.
- **Language servers:** Support for Bash, Dockerfile, JavaScript/TypeScript, and SQL for enhanced code completion and linting.
- **Spanish language pack:** JupyterLab interface available in Spanish.

## Installed Kernels

- **Python** (default, via Jupyter minimal-notebook)
- **Java** (IJava kernel)
- **JavaScript** (IJavascript kernel)
- **C** (jupyter-c-kernel)
- **SQL** (xeus-sqlite kernel)

## Usage Instructions

1. **Build the Docker image:**
	```powershell
	docker build -t jupyter-student-stack .
	```

2. **Run the container:**
	```powershell
	docker run -p 8888:8888 jupyter-student-stack
	```

3. **Access JupyterLab:**
	Open your browser and go to [http://localhost:8888](http://localhost:8888). Copy the token from the container logs if required.

4. **Select a kernel:**
	When creating a new notebook, choose from the available kernels (Python, Java, JavaScript, C, SQL) depending on your course or activity.

## Educational Focus

This image is tailored for use in schools, universities, and workshops. It provides:

- A consistent environment for students and instructors.
- Tools for assignments, grading, and collaborative work.
- Support for multiple programming languages commonly taught in computer science and engineering courses.

## Extensions

- **nbgrader:** Assignment and grading management.
- **nbgitpuller:** Easy distribution of materials.
- **Resource Usage:** Monitor notebook resource consumption.
- **Variable Inspector:** Inspect variables in notebooks.
- **RISE:** Turn notebooks into interactive slideshows.

