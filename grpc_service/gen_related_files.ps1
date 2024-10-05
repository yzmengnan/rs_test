
Set-Location .

conda env list

conda init

conda activate rs_test

python -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. ./services.proto