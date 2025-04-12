docker build -t pastry:latest .
mkdir -p ./artifacts
docker save pastry:latest -o ./artifacts/pastry.tar