from ipykernel.kernelapp import IPKernelApp

from .kernel import AsmKernel

IPKernelApp.launch_instance(kernel_class=AsmKernel)
