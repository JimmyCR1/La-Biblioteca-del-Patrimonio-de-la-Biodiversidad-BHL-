from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
from psycopg2 import Error as psycopg2Error

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Función para obtener una conexión con la base de datos PostgreSQL.
# En caso de error, imprime un mensaje y devuelve None.
def get_db_connection():
    try:
        return psycopg2.connect(
            host="localhost",
            database="Libros_Asquerosos",
            user="postgres",
            password="89562772"
        )
    except psycopg2Error as e:
        print(f"Error de base de datos: {e}")
        return None

# Ruta principal que muestra la página de inicio.
# Renderiza el archivo HTML 'index.html'.
@app.route('/')
def index():
    return render_template('index.html')

# Ruta para agregar una nueva publicación.
# Si el método de la solicitud es POST, se insertan los datos en la base de datos.
# Después de la inserción, redirige a una página para agregar autores, especies y colecciones.
@app.route('/add_publication', methods=['GET', 'POST'])
def add_publication():
    # Establecer conexión a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        # Obtener los datos enviados desde el formulario
        title = request.form['title']
        publication_date = request.form['publication_date']
        publisher = request.form['publisher']
        doi = request.form['doi']
        isbn = request.form['isbn']
        country = request.form['country']
        institution_id = request.form['institution_id']

        # Insertar la nueva publicación en la tabla 'publications'
        cursor.execute('''
            INSERT INTO publications (title, publication_date, publisher, doi, isbn, country, institution_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING publication_id
        ''', (title, publication_date, publisher, doi, isbn, country, institution_id))

        # Obtener el ID de la publicación recién creada
        publication_id = cursor.fetchone()[0]

        # Confirmar los cambios y cerrar la conexión
        conn.commit()
        cursor.close()
        conn.close()

        # Redirigir a la ruta 'extras_add' para agregar más información relacionada con la publicación
        return redirect(url_for('extras_add', publication_id=publication_id))
    
    # Si el método es GET, renderizar el formulario de 'add_publication.html'
    return render_template('add_publication.html')




# Ruta para agregar autores, especies y colecciones a una publicación existente.
# Se recibe el 'publication_id' de la publicación a la que se asociarán los datos.
@app.route('/extras_add/<int:publication_id>', methods=['GET', 'POST'])
def extras_add(publication_id):
    # Establecer conexión a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        # Obtener datos del formulario enviados por el usuario
        author_ids = request.form.getlist('authors')
        species_ids = request.form.getlist('species')
        collection_ids = request.form.getlist('collections')

        # Asociar autores a la publicación
        for author_id in author_ids:
            cursor.execute('''
                INSERT INTO publication_authors (publication_id, author_id)
                VALUES (%s, %s)
            ''', (publication_id, author_id))

        # Asociar especies a la publicación
        for species_id in species_ids:
            cursor.execute('''
                INSERT INTO publication_species (publication_id, species_id)
                VALUES (%s, %s)
            ''', (publication_id, species_id))

        # Asociar colecciones a la publicación
        for collection_id in collection_ids:
            cursor.execute('''
                INSERT INTO publication_collections (publication_id, collection_id)
                VALUES (%s, %s)
            ''', (publication_id, collection_id))

        # Confirmar los cambios y cerrar la conexión
        conn.commit()
        cursor.close()
        conn.close()

        # Redirigir a la página principal u otra página deseada
        return redirect(url_for('index'))

    # Si el método es GET, obtener listas de autores, especies y colecciones para mostrar en el formulario
    cursor.execute('SELECT author_id, first_name, last_name FROM authors')
    authors = cursor.fetchall()

    cursor.execute('SELECT species_id, genus, species FROM species')
    species = cursor.fetchall()

    cursor.execute('SELECT collection_id, name FROM collections')
    collections = cursor.fetchall()

    # Cerrar cursor y conexión
    cursor.close()
    conn.close()

    # Renderizar la plantilla 'extras_add.html' con los datos obtenidos y el ID de la publicación
    return render_template('extras_add.html', publication_id=publication_id, authors=authors, species=species, collections=collections)






# Ruta para ver todas las publicaciones disponibles.
# Se realiza una consulta a la base de datos para obtener todos los registros de publicaciones y se renderiza una plantilla.
@app.route('/view_publications')
def view_publications():
    # Establecer conexión con la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()

    # Realizamos la consulta para obtener todas las publicaciones
    cursor.execute('SELECT publication_id, title, publication_date, publisher FROM publications')
    publications = cursor.fetchall()

    # Cerrar la conexión
    conn.close()

    # Renderiza la plantilla 'view_publications.html' con los datos de las publicaciones obtenidos
    return render_template('view_publications.html', publications=publications)



# Ruta para editar una publicación existente.
# Permite editar los detalles de la publicación y las asociaciones con autores, especies y colecciones.
@app.route('/edit_publication/<int:publication_id>', methods=['GET', 'POST'])
def edit_publication(publication_id):
    # Establecer conexión con la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        # Obtener los datos del formulario
        title = request.form['title']
        publication_date = request.form['publication_date']
        publisher = request.form['publisher']
        doi = request.form['doi']
        isbn = request.form['isbn']
        country = request.form['country']
        institution_id = request.form['institution_id']

        # Validar el campo institution_id para asegurarse de que sea un número válido
        if institution_id and institution_id.isdigit():
            institution_id = int(institution_id)
        else:
            institution_id = None  # Establecer a None si no es válido

        # Actualizar los detalles de la publicación en la base de datos
        cursor.execute('''
            UPDATE publications
            SET title = %s, publication_date = %s, publisher = %s, doi = %s, isbn = %s, country = %s, institution_id = %s
            WHERE publication_id = %s
        ''', (title, publication_date, publisher, doi, isbn, country, institution_id, publication_id))

        # Obtener los IDs de autores, especies y colecciones seleccionados desde el formulario
        author_ids = request.form.getlist('authors')
        species_ids = request.form.getlist('species')
        collection_ids = request.form.getlist('collections')

        # Actualizar las asociaciones de autores
        cursor.execute('DELETE FROM publication_authors WHERE publication_id = %s', (publication_id,))
        for author_id in author_ids:
            cursor.execute('INSERT INTO publication_authors (publication_id, author_id) VALUES (%s, %s)', (publication_id, author_id))

        # Actualizar las asociaciones de especies
        cursor.execute('DELETE FROM publication_species WHERE publication_id = %s', (publication_id,))
        for species_id in species_ids:
            cursor.execute('INSERT INTO publication_species (publication_id, species_id) VALUES (%s, %s)', (publication_id, species_id))

        # Actualizar las asociaciones de colecciones
        cursor.execute('DELETE FROM publication_collections WHERE publication_id = %s', (publication_id,))
        for collection_id in collection_ids:
            cursor.execute('INSERT INTO publication_collections (publication_id, collection_id) VALUES (%s, %s)', (publication_id, collection_id))

        # Confirmar los cambios en la base de datos
        conn.commit()

        # Mostrar un mensaje de éxito y redirigir a la vista de todas las publicaciones
        flash('Publicación actualizada con éxito', 'success')
        return redirect(url_for('view_publications'))

    # Si el método es GET, obtener los detalles actuales de la publicación
    cursor.execute('SELECT title, publication_date, publisher, doi, isbn, country, institution_id FROM publications WHERE publication_id = %s', (publication_id,))
    publication = cursor.fetchone()

    # Obtener todos los autores, especies y colecciones disponibles para mostrarlos en el formulario
    cursor.execute('SELECT author_id, first_name, last_name FROM authors')
    authors = cursor.fetchall()

    cursor.execute('SELECT species_id, genus, species FROM species')
    species = cursor.fetchall()

    cursor.execute('SELECT collection_id, name FROM collections')
    collections = cursor.fetchall()

    # Obtener las asociaciones actuales de la publicación (autores, especies, colecciones)
    cursor.execute('SELECT author_id FROM publication_authors WHERE publication_id = %s', (publication_id,))
    associated_authors = [row[0] for row in cursor.fetchall()]

    cursor.execute('SELECT species_id FROM publication_species WHERE publication_id = %s', (publication_id,))
    associated_species = [row[0] for row in cursor.fetchall()]

    cursor.execute('SELECT collection_id FROM publication_collections WHERE publication_id = %s', (publication_id,))
    associated_collections = [row[0] for row in cursor.fetchall()]

    # Cerrar el cursor y la conexión
    cursor.close()
    conn.close()

    # Renderizar la plantilla 'edit_publication.html' con los datos obtenidos
    return render_template('edit_publication.html', 
                           publication=publication, 
                           authors=authors, 
                           species=species, 
                           collections=collections, 
                           associated_authors=associated_authors, 
                           associated_species=associated_species, 
                           associated_collections=associated_collections)




# Ruta para eliminar una publicación específica.
# Elimina primero las relaciones en las tablas intermedias (autores, especies, colecciones) y luego la publicación en sí.
@app.route('/delete_publication/<int:publication_id>', methods=['POST'])
def delete_publication(publication_id):
    # Reutilizamos la función de conexión existente
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Eliminar relaciones con autores, especies y colecciones
        cursor.execute("DELETE FROM publication_authors WHERE publication_id = %s", (publication_id,))
        cursor.execute("DELETE FROM publication_species WHERE publication_id = %s", (publication_id,))
        cursor.execute("DELETE FROM publication_collections WHERE publication_id = %s", (publication_id,))

        # Eliminar la publicación de la base de datos
        cursor.execute("DELETE FROM publications WHERE publication_id = %s", (publication_id,))

        # Confirmar los cambios
        conn.commit()

    except Exception as e:
        # Si ocurre un error, se realiza un rollback para deshacer los cambios
        conn.rollback()
        raise e  # Relanzar el error para que pueda ser manejado en otro lugar si es necesario

    finally:
        # Cerrar el cursor y la conexión a la base de datos
        cursor.close()
        conn.close()

    # Redirigir a la página que muestra todas las publicaciones
    return redirect(url_for('view_publications'))

# Ruta para consultar publicaciones por especie.
# Realiza una búsqueda de publicaciones en función del nombre científico de una especie proporcionada por el usuario.
@app.route('/consult_by_species', methods=['GET', 'POST'])
def consult_by_species():
    # Establecer conexión con la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()

    publications = []  # Lista vacía para almacenar las publicaciones encontradas
    if request.method == 'POST':
        species_name = request.form['species_name']  # Obtener el nombre de la especie del formulario

        # Realizar la consulta para encontrar publicaciones asociadas a la especie ingresada
        cursor.execute('''
            SELECT p.publication_id, p.title, p.publication_date, p.publisher
            FROM publications p
            JOIN publication_species ps ON p.publication_id = ps.publication_id
            JOIN species s ON ps.species_id = s.species_id
            WHERE LOWER(s.genus || ' ' || s.species) = LOWER(%s)
        ''', (species_name.strip(),))  # strip() para eliminar posibles espacios en blanco al inicio y final del nombre
        publications = cursor.fetchall()

    # Cerrar la conexión
    conn.close()

    # Renderizar la plantilla 'consult_by_species.html' con las publicaciones encontradas
    return render_template('consult_by_species.html', publications=publications)

# Ruta para ver los detalles de una publicación específica.
# Muestra los detalles de la publicación, autores, especies y colecciones asociadas.
@app.route('/view_publication/<int:publication_id>')
def view_publication(publication_id):
    # Establecer conexión con la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()

    # Obtener los detalles de la publicación
    cursor.execute('''
        SELECT p.title, p.publication_date, p.publisher, p.doi, p.isbn, p.country
        FROM publications p
        WHERE p.publication_id = %s
    ''', (publication_id,))
    publication = cursor.fetchone()

    # Obtener los autores asociados a la publicación
    cursor.execute('''
        SELECT a.first_name, a.last_name
        FROM authors a
        JOIN publication_authors pa ON a.author_id = pa.author_id
        WHERE pa.publication_id = %s
    ''', (publication_id,))
    authors = cursor.fetchall()

    # Obtener las especies asociadas a la publicación
    cursor.execute('''
        SELECT s.genus, s.species
        FROM species s
        JOIN publication_species ps ON s.species_id = ps.species_id
        WHERE ps.publication_id = %s
    ''', (publication_id,))
    species = cursor.fetchall()

    # Obtener las colecciones asociadas a la publicación
    cursor.execute('''
        SELECT c.name
        FROM collections c
        JOIN publication_collections pc ON c.collection_id = pc.collection_id
        WHERE pc.publication_id = %s
    ''', (publication_id,))
    collections = cursor.fetchall()

    # Cerrar cursor y conexión
    cursor.close()
    conn.close()

    # Renderizar la plantilla 'view_publication.html' con los detalles de la publicación y sus asociaciones
    return render_template('view_publication.html', publication=publication, authors=authors, species=species, collections=collections)




# Ruta para consultar publicaciones por colección.
# Permite seleccionar una colección y ver las publicaciones asociadas a ella.
@app.route('/consult_by_collection', methods=['GET', 'POST'])
def consult_by_collection():
    # Establecer conexión con la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()

    collections = []  # Lista para almacenar todas las colecciones disponibles
    publications = []  # Lista para almacenar las publicaciones encontradas
    collection_name = None  # Variable para almacenar el nombre de la colección seleccionada

    if request.method == 'POST':
        # Obtener el ID de la colección seleccionada del formulario
        collection_id = request.form['collection_id']

        # Obtener el nombre de la colección seleccionada
        cursor.execute('SELECT name FROM collections WHERE collection_id = %s', (collection_id,))
        collection_name = cursor.fetchone()[0]  # Almacenar el nombre de la colección

        # Obtener las publicaciones asociadas a la colección seleccionada
        cursor.execute('''
            SELECT p.publication_id, p.title, p.publication_date, p.publisher
            FROM publications p
            JOIN publication_collections pc ON p.publication_id = pc.publication_id
            WHERE pc.collection_id = %s
        ''', (collection_id,))
        publications = cursor.fetchall()  # Almacenar las publicaciones encontradas

    else:
        # Si es una solicitud GET, obtener todas las colecciones para mostrarlas en el formulario
        cursor.execute('SELECT collection_id, name FROM collections')
        collections = cursor.fetchall()  # Almacenar todas las colecciones disponibles

    # Cerrar cursor y conexión a la base de datos
    cursor.close()
    conn.close()

    # Renderizar la plantilla 'consult_by_collection.html' pasando las colecciones, publicaciones y el nombre de la colección seleccionada
    return render_template('consult_by_collection.html', collections=collections, publications=publications, collection_name=collection_name)


if __name__ == '__main__':
    app.run(debug=True)
