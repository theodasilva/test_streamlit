# 1) Lance l’application Streamlit en local.
#    URL par défaut : http://localhost:8501
run:
	streamlit run Index.py


# 2) Met automatiquement le code au format :
#    • black  → style PEP 8 / 88 car.
#    • isort  → ordonner les imports.
format:
	black .
	isort .


# 3) Installe toutes les dépendances Python
#    définies dans requirements.txt dans
#    l’environnement virtuel actif.
install:
	python3 -m pip install -r requirements.txt