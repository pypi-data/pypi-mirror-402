![Static Badge](https://img.shields.io/badge/python-3.12%2B-blue)
![Static Badge](https://img.shields.io/badge/license-%20%20GNU%20GPLv3+%20-red?style=plastic)
![GitHub last commit](https://img.shields.io/github/last-commit/mikemolina/kronolapse)
![GitHub Tag](https://img.shields.io/github/v/tag/mikemolina/kronolapse)

# KRoNoLAPSE

<video src="https://github.com/user-attachments/assets/487f8c54-1d6d-4d69-bf85-ff359997944f" controls width="400"></video>

**kronolapse** es una herramienta en Python que gestiona la visualización de
contenidos, automatizando la exhibición de imágenes en un monitor según horarios
(`cronograma`) y tiempos (`lapsos`) personalizados, garantizando la presentación
correcta del contenido en el momento preciso.

## ¡Características clave!
- **Planeación sencilla.** Los contenidos, horarios y su duración son planificados
  en un archivo de texto plano.
- **Uso simple.** Aunque **kronolapse** usa una Interfaz de Línea de Comandos
  (CLI), después de instalado, en la terminal predeterminada de tu sistema,
  simplemente ejecuta la herramienta con la planeación guardada en el archivo de
  texto.
- **Visualización de contenidos.** Inicialmente, **kronolapse** admite formatos de
  imagen convencionales como JPG, PNG, BMP.

## Instalación
### Modo usuario
1. [Python](https://www.python.org/downloads/) y
   [pip](https://pip.pypa.io/en/stable/installation/#get-pip-py) deben estar
   instalados en tu sistema. Es recomendable la versión 3.12 o superior para
   Python.
2. Instalar la última versión desde el repositorio con esta linea
   (requiere `Git`):

   ```bash
   pip install git+https://github.com/mikemolina/kronolapse.git
   ```

### Modo desarrollador
1. [Python](https://www.python.org/downloads/),
   [pip](https://pip.pypa.io/en/stable/installation/#get-pip-py) y [GNU
   Make](https://www.gnu.org/software/make/) deben estar instalados en tu
   sistema. Es recomendable la versión 3.12 o superior para Python. Para GNU Make
   en distribuciones Linux/macOS, consulte su respectivo gestor de paquetes; en
   Windows, él está incluido en las herramientas pre-compiladas de la colección
   [mingw-w64](https://www.mingw-w64.org/).

2. Clonar el repositorio y navegar hacia su directorio:

   ```bash
   git clone https://github.com/mikemolina/kronolapse.git kronolapse-dev
   cd kronolapse-dev
   ```

3. Preparar un entorno virtual y compilar el paquete. Requiere el paquete
   [virtualenv](https://pypi.org/project/virtualenv/) instalado en tu sistema.

   ```bash
   make prepare-venv
   make build
   ```

4. Instalar el paquete en modo editable dentro del entorno virtual:

   ```bash
   make install
   ```

   Dependencias requeridas como
   [opencv-python](https://pypi.org/project/opencv-python/) y
   [screeninfo](https://pypi.org/project/screeninfo/) son instaladas
   automáticamente en este paso.

## Uso
### Modo usuario
1. Planifique en un archivo de texto plano con formato
   [CSV](https://es.wikipedia.org/wiki/Valores_separados_por_comas) los
   contenidos, horarios y su duración. La duración de la exhibición está
   determinada por el tiempo inicial y el tiempo final.

   El `archivo CSV` debe tener tres campos o columnas separados por comas (`,`) y
   la primera línea debe iniciar con un encabezado similar a:

   > Documento imagen,Tiempo inicial,Tiempo final

   En seguida, listar cada imagen con su ruta absoluta (según el sistema
   operativo), el tiempo inicial y tiempo final de la exhibición; los tiempos son
   ingresados en [formato ISO 8601](https://es.wikipedia.org/wiki/ISO_8601), esto
   es, en formato _YYYY-mm-dd HH:mm:ss_. Como ejemplo de una lista de
   programación, aquí se muestra un ejemplo para un sistema Windows:

   ```none
   Documento imagen,Tiempo inicial,Tiempo final
   C:\Users\usuario\Documents\imagen-1.jpg,2025-12-01 09:00:00,2025-12-01 09:04:59
   C:\Users\usuario\Documents\imagen-2.jpg,2025-12-01 09:05:00,2025-12-01 09:07:00
   ```

   Finalmente guardar el archivo CSV; por ejemplo, como `cronograma.csv`.

2. Desde la terminal, usar:

   ```bash
   kronolapse ruta\a\cronograma.csv
   ```

### Modo desarrollador
Los archivos de presentación deben tener formato JPG, PNG o formato de imagen
soportado por [OpenCV](https://docs.opencv.org/4.x/db/deb/tutorial_display_image.html).

**Recomendación.** Los tiempos inicial y final del cronograma para cada archivos
no deben coincidir para evitar la superposición o solapamiento de dos imágenes
simultaneas.

1. Diseñar una programación como se indico anteriormente y desde la terminal,
   usar:

   ```bash
   python3 -m kronolapse ruta/a/cronograma.csv
   ```

2. Para una demostración automatizada usar:

   ```bash
   make run
   ```

3. Una secuencia de pruebas es ejecutada con:

   ```bash
   make tests
   ```

   Requiere [pytest](https://pypi.org/project/pytest/) y
   [pillow](https://pypi.org/project/pillow/).

4. Para más opciones, usar:

   ```bash
   $ python3 -m kronolapse --help
   ```

5. La documentación del código fuente es compilada vía
   [Sphinx](https://www.sphinx-doc.org/en/master/). Usando siguiente la orden, se
   instalaran los respectivos paquetes y sus dependencias en el entorno virtual,
   
   ```bash
   make prepare-sphinx
   ```
   
   Con lo anterior, se puede construir la documentación en formatos HTML, página
   de manual ([documentación típica](https://en.wikipedia.org/wiki/Man_page) para
   sistemas UNIX) y PDF (requiere [TeX Live](https://www.tug.org/texlive/) o
   [MiKTeX](https://miktex.org/) instalado en su sistema):
   
   ```bash
   make html
   make man
   make pdf
   ```

## Diagrama de flujo para kronolapse

<p align="center">
  <img src="extra/dgrm-kronolapse.jpg" width="70%"/>
</p>

El diagrama de flujo fue desarrollado en [draw.io](https://www.drawio.com/).

## Bugs
- En sistemas operativos Linux, con monitores 4K usando escalado fraccional
  (entorno de escritorio GNOME), la exhibición no se muestra en pantalla completa.

## Licencia
**kronolapse** es software libre y se distribuye bajo los términos de la Licencia
Pública General de GNU, versión 3 o posterior, incluida con el código fuente del
paquete en el archivo _LICENSE_.

## Acerca del versionado
Este proyecto sigue los lineamientos de [Versionado Semántico
2.0.0](https://semver.org/spec/v2.0.0.html).

## Documentación
Consulte el documento más reciente
[aquí](https://github.com/mikemolina/kronolapse/blob/main/extra/kronolapse.pdf).
