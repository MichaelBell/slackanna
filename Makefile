all: wordfind.proto
	python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. wordfind.proto
