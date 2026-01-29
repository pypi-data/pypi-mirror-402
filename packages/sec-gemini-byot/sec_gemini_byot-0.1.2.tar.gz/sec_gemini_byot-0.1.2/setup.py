import os
import subprocess
import sys
from setuptools import setup, find_packages
from setuptools.command.build_py import build_py

class BuildPyCommand(build_py):
    def run(self):
        # Path to the proto file
        proto_path = os.path.join("common", "hub.proto")
        
        if os.path.exists(proto_path):
            print(f"Compiling {proto_path}...")
            try:
                import grpc_tools.protoc
                # We want the output to be inside the package
                output_dir = os.path.join("src", "sec_gemini_byot")
                os.makedirs(output_dir, exist_ok=True)
                
                grpc_tools.protoc.main([
                    'grpc_tools.protoc',
                    '-Icommon',
                    f'--python_out={output_dir}',
                    f'--grpc_python_out={output_dir}',
                    proto_path,
                ])
                
                # Fix imports in generated files for Python 3 relative imports
                # The generated hub_pb2_grpc.py might have "import hub_pb2"
                # which needs to be "from . import hub_pb2" if we want it to work as a package.
                generated_grpc = os.path.join(output_dir, "hub_pb2_grpc.py")
                if os.path.exists(generated_grpc):
                    with open(generated_grpc, 'r') as f:
                        content = f.read()
                    content = content.replace('import hub_pb2 as hub__pb2', 'from . import hub_pb2 as hub__pb2')
                    with open(generated_grpc, 'w') as f:
                        f.write(content)
                        
            except ImportError:
                print("grpcio-tools not found during build, skipping proto compilation")
        else:
            print(f"Warning: {proto_path} not found")
        
        super().run()

if __name__ == "__main__":
    setup(
        cmdclass={
            'build_py': BuildPyCommand,
        },
    )
