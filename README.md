# Jupyter Student Stack

Jupyter Student Stack is a set of Docker images designed for educational environments, providing a ready-to-use JupyterLab setup with multiple programming language kernels, example notebooks and useful extensions for teaching and learning.

## Features

- **Multi-language support:** Kernels for Python, Bash, Java, JavaScript/TypeScript, C, SQL and x86-64 Assembly.
- **One image per language, or all of them:** pick the smallest image that fits your course.
- **Example notebooks:** every image includes `examples/` with the basics of each of its languages, refreshed on every start.
- **Pre-installed extensions:** nbgrader, nbgitpuller, resource usage monitor, variable inspector, and JupyterLab RISE for presentations.
- **Language servers:** code completion and diagnostics through jupyterlab-lsp (Python, Bash, and JavaScript/TypeScript and SQL in their images).
- **Spanish language pack:** JupyterLab interface available in Spanish.

## Image Variants

Every image includes Python and Bash. The full image includes everything.

| Image | Kernels | Pull |
|---|---|---|
| full | Python, Bash, Java, JavaScript/TypeScript, C, SQL, Assembly | `docker pull cavefish/jupyter-student-stack:latest` |
| python | Python, Bash | `docker pull cavefish/jupyter-student-stack:python-latest` |
| java | Python, Bash, Java | `docker pull cavefish/jupyter-student-stack:java-latest` |
| javascript | Python, Bash, JavaScript/TypeScript | `docker pull cavefish/jupyter-student-stack:javascript-latest` |
| c | Python, Bash, C | `docker pull cavefish/jupyter-student-stack:c-latest` |
| sql | Python, Bash, SQL | `docker pull cavefish/jupyter-student-stack:sql-latest` |
| asm | Python, Bash, x86-64 Assembly | `docker pull cavefish/jupyter-student-stack:asm-latest` |

Each image is published for `amd64` and `arm64`; add `-amd64` or `-arm64` to a tag to pick one architecture (e.g. `java-latest-amd64`).

## Installed Kernels

- **Python** (via Jupyter minimal-notebook)
- **Bash** (bash_kernel)
- **Java** (JJava, the maintained successor of IJava)
- **JavaScript / TypeScript** (Deno kernel)
- **C** (jupyter-c-kernel: each cell is compiled and run as a whole program)
- **SQL** (xeus-sqlite kernel)
- **x86-64 Assembly** (NASM syntax, this repo's [step-by-step kernel](kernels/asm): an emulated CPU shows the registers after every cell and highlights what changed; same behaviour on amd64 and arm64)

## Example Notebooks

Each image contains the notebooks for its languages in `~/examples` (see [examples/](examples)). They are copied fresh from the image every time the server starts, so students always get the latest version and can't break them for good. **Copy a notebook into `work/` to keep your changes.**

## Usage Instructions

1. **Obtain the image from Docker Hub:**
	```powershell
	docker pull cavefish/jupyter-student-stack
	```

	Or build locally (`--target` picks the variant; the default is `full`):
	```powershell
	docker build -t jupyter-student-stack .
	docker build --target java -t jupyter-student-stack:java .
	```

2. **Run the container:**
	```powershell
	docker run -p 8888:8888 jupyter-student-stack
	```

3. **Access JupyterLab:**
	Open your browser and go to [http://localhost:8888](http://localhost:8888). Copy the token from the container logs if required.

4. **Select a kernel:**
	When creating a new notebook, choose from the available kernels depending on your course or activity, or start from one of the notebooks in `examples/`.

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
- **jupyterlab-lsp:** Code completion, hover help and diagnostics from language servers.

## Testing

- ASM kernel unit tests: `docker build -f kernels/asm/Dockerfile.test -t asm-kernel-test kernels/asm && docker run --rm asm-kernel-test`
- Run every example notebook in an image: `bash ci/test-examples.sh <image>`
