#!/bin/bash
# IPv7 Automated Linux/macOS Installer
echo -e "\033[0;36mIniciando instalacion automatica de IPv7...\033[0m"

# 1. Verificar Python
if ! command -v python3 &> /dev/null
then
    echo -e "\033[0;31mError: Python3 no esta instalado.\033[0m"
    exit 1
fi

# 2. Crear entorno virtual
if [ ! -d "venv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv venv
fi

# 3. Instalar dependencias
echo "Instalando dependencias desde requirements.txt..."
./venv/bin/python3 -m pip install --upgrade pip
./venv/bin/pip install -r requirements.txt
./venv/bin/pip install -e .

# 4. Crear acceso directo CLI
cat <<EOF > ipv7
#!/bin/bash
export PYTHONPATH=\$PYTHONPATH:\$(pwd)
./venv/bin/python3 \$(pwd)/ipv7/cli.py "\$@"
EOF
chmod +x ipv7

echo -e "\n\033[0;32m[✓] IPv7 instalado correctamente!\033[0m"
echo "Puedes usar './ipv7 status' para verificar."
echo "Para lanzar la GUI: './venv/bin/python3 gui/server.py'"
