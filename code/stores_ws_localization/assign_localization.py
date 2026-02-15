# Script to obtain the address and coordinates of stores from Google Maps API
import requests
import csv
import os
import time
from dotenv import load_dotenv
import unicodedata

load_dotenv()  # load from .env file
apiKey = os.getenv("GOOGLE_MAPS_API_KEY")

input_file_list = [
    "../../data/chains/raw_data/tienda_ara.csv", 
    "../../data/chains/raw_data/d1.csv", 
    "../../data/chains/raw_data/justo_y_bueno.csv", 
    "../../data/chains/raw_data/oxxos.csv"
    ]

temp_file_list = [
    "../../data/chains/tienda_ara_shops_progress.csv", 
    "../../data/chains/d1_shops_progress.csv", 
    "../../data/chains/justo_y_bueno_shops_progress.csv", 
    "../../data/chains/oxxo_shops_progress.csv"
    ]

#camaras de comercio to be sure that the location is correct
camaras_de_comercio = {
    "ABURRA SUR":{
        "departamento": ["ANTIOQUIA"],
        "municipios":["Caldas", "Envigado", "La Estrella", "Sabaneta", "Itagüi"]
    },
    "AGUACHICA":{
        "departamento": ["CESAR", "BOLIVAR"],
        "municipios":["Curumaní", "Pailitas", "San Alberto", "Pelaya", "San Martín", "Río de Oro", "Tamalameque", "La Gloria", "Gamarra", "González", "Morales", "Santa Rosa del Sur", "Simití", "Arenal", "Regidor", "Río Viejo y Norosí"]
    }, 
    "ARAUCA":{
        "departamento": ["ARAUCA"],
        "municipios":[]
    },
    "ARMENIA":{
        "departamento": ["QUINDIO"],
        "municipios":[]
    },
    "BARRANCABERMEJA":{
        "departamento": ["SANTANDER"],
        "municipios":["Barrancabermeja", "Cimitarra", "El Carmen", "Puerto Parra", "Puerto Wilches", "Sabana de Torres", "San Vicente de Chucurí", "Cantagallo", "San Pablo"]
    },
    "BARRANQUILLA":{
        "departamento": ["ATLANTICO", "MAGDALENA"],
        "municipios":["Cerro de San Antonio", "Pedraza", "Remolino", "Sitio Nuevo"]
    },
    "BOGOTA":{
        "departamento": ["CUNDINAMARCA", "BOGOTA"],
        "municipios":["Bogota", "Arbeláez", "Cabrera", "Cajicá", "Cáqueza", "Carmen de Garupa", "Chía", "Chipaque", "Choachí", "Chocontá", "Cogua", "Cota", "Cucunubá", "Fómeque", "Fosca", "Fúquene", "Fusagasugá", "Gachalá", "Gachancipá", "Gachetá", "Gama", "Granada", "Guachetá", "Guasca", "Guatavita", "Guayabetal", "Gutiérrez", "Junín", "La Calera", "Lenguazaque", "Machetá", "Manta", "Medina", "Nemocón", "Pandi", "Pasca", 	"Quetame","San Bernardo","Sesquilé","Sibaté","Silvania","Simijaca","Soacha","Sopó","Suesca","Susa","Sutatausa","Tabio","Tausa","Tenjo","Tibacuí","Tibirita","Tocancipá","Ubalá","Ubaque","Ubaté","Une","Venecia","Villapinzón y Zipaquirá"]
    },
    "BUCARAMANGA":{ 
        "departamento": ["SANTANDER"],
        "municipios":["Bucaramanga", "Aguada", "Albania", "Aratoca", "Barbosa", "Barichara", "Betulia", "Bolívar", "Cabrera", "California", "Capitanejo", "Carcasí", "Cepita", "Cerrito", "Concepción", "Confines", "Contratación", "Coromoro", "Curití", "Charalá", "Charta", "Chima", "Chipatá", "Guacamayo", "El Peñón", "El Playón", "Enciso", "Encino", "Florián", "Floridablanca", "Galán", "Gámbita", "Girón", "Guaca", "Guadalupe", "Guapotá", "Guavatá", "Güepsa", "Hato", "Jesús María", "Jordán" ,"La Belleza", "Landázuri", "La Paz", "Lebrija", "Los Santos", "Macaravita", "Málaga", "Matanza", "Mogotes", "Molagavita", "Ocamonte", "Oiba", "Onzaga", "Palmar", "Palmas del Socorro", "Páramo", "Piedecuesta", "Pinchote", "Puente Nacional", "Rionegro", "San Andrés", "San Benito", "San Gil", "San Joaquín", "San José de Miranda", "San Miguel", "Santa Bárbara", "Santa Helena del Opón", "Simacota", "Socorro", "Suaita", "Sucre", "Suratá" ,"Tona" ,"Umpalá" ,"Valle de San José" ,"Vélez" ,"Vetas" ,"Villanueva", "Zapatoca"]
    },
    "BUENAVENTURA":{
        "departamento": ["VALLE DEL CAUCA", "CAUCA"],
        "municipios":["Buenaventura", "Guapi"] 
    },
    "BUGA":{
        "departamento": ["VALLE DEL CAUCA"],
        "municipios":["Buga", "Calima - Darién", "El Cerrito", "Ginebra", "Guacarí", "Restrepo", "San Pedro", "Yotoco"] 
    },
    "CALI":{
        "departamento": ["VALLE DEL CAUCA"],
        "municipios":["Cali", "Dagua", "Jamundí", "La Cumbre", "Vijes", "Yumbo"]
    },
    "CARTAGENA":{
        "departamento": ["BOLIVAR"],
        "municipios":["Cartagena", "Arjona", "Arroyohondo", "Calamar", "Carmen de Bolívar", "Clemencia", "ElGuamo", "Mahates", "María La Baja", "San Cristóbal", "San Estanislao", "San Jacinto", "San Juan Nepomuceno", "Santa Catalina", "Santa Rosa", "Soplaviento", "Turbaco", "Turbaná y Villanueva"]
    },
    "CARTAGO":{
        "departamento": ["VALLE DEL CAUCA", "CHOCO"],
        "municipios":["Cartago", "Alcalá", "Ansermanuevo", "Argelia", "El Aguila", "El Cairo", "El Dovio", "La Unión", "La Victoria", "Obando", "Roldanillo", "Toro", "Ulloa", "Versalles", "San José del Palmar"]  
    },
    "CASANARE":{
        "departamento": ["CASANARE"],
        "municipios":[]
    },
    "CAUCA":{
        "departamento": ["CAUCA"],
        "municipios":[]
    },
    "CHINCHINA":{
        "departamento": ["CALDAS"], 
        "municipios": ["Chinchina", "Palestina"]
    },
    "CHOCO":{
        "departamento": ["CHOCO"],
        "municipios":[]
    },
    "CUCUTA":{  
        "departamento": ["NORTE DE SANTANDER"],
        "municipios":["Cúcuta", "Arboledas", "Bucarasica", "Chinácota", "Durania", "El Zulia", "Gramalote", "Herrán", "Los Patios", "Lourdes", "Puerto Santander", "Ragonvalia", "Salazar", "San Cayetano", "Santiago", "Sardinata", "Tibú" , "Villa del Rosario"]
    },
    "DOSQUEBRADAS":{
        "departamento": ["RISARALDA"],
        "municipios":["Dosquebradas"]
    },
    "DUITAMA":{
        "departamento": ["BOYACA"],
        "municipios":["Duitama", "Belén", "Boavita", "Cerinza", "Chiscas", "Chita", "Covarachía", "El Cocuy", "El Espino", "Floresta", "Guacamayas", "Güicán", "Jericó", "La Uvita", "Paipa", "Panqueba", "Paz del Río", "San Mateo", "Santa Rosa de Viterbo", "Sativa norte", "Sativa sur", "Soatá", "Socotá", "Socha", "Sotaquirá", "Susacón", "Tasco", "Tipacoque", "Tutasá","Tuta"]
    },
    "FACATATIVA":{
        "departamento": ["CUNDINAMARCA"],
        "municipios":[ "Facatativá", "Albán", "Anolaima", "Beltrán", "Bituima", "Bojacá", "Cachipay", "Caparrapí", "Chaguaní", "El Peñón", "El Rosal", "Funza", "Guayabal de Síquima", "La Palma", "La Peña", "La Vega", "Madrid", "Mosquera", "Nimaima", "Nocaima", "Sasaima", "San Cayetano", "San Francisco", "San Juan de Rioseco", "Subachoque", "Supatá", "Topaipí", "Pacho", "Paime", "Quebradanegra", "Vergara", "Vianí", "Villeta", "Villagómez", 	"Yacopí","Utica","Zipacón"]
    },
    "GIRARDOT":{
        "departamento": ["CUNDINAMARCA"],
        "municipios":["Girardot", "Agua de Dios", "Anapoima", "Apulo", "El Colegio", "Guataquí", "Jerusalén", "La Mesa", "Nariño", "Nilo", "Pulí", "Quipile", "Ricaurte", "San Antonio del Tequendama", "Tena", "Tocaima", "Viotá"]
    },
    "HONDA":{
        "departamento": ["TOLIMA", "CUNDINAMARCA"],
        "municipios":["Honda", "Ambalema", "Armero Guayabal", "Casabianca", "Falan", "Fresno", "Herveo", "Lérida", "Líbano", "Mariquita", "Murillo", "Palocabildo y Villahermosa"]
    },
    "HUILA":{
        "departamento": ["HUILA"],
        "municipios":[]
    },
    "IBAGUE":{
        "departamento": ["TOLIMA"],
        "municipios":["Ibagué", "Alvarado", "Anzoátegui", "Cajamarca", "Piedras", "Roncesvalles", "Rovira", "San Antonio", "Santa Isabel", "Valle de San Juan", "Venadillo"]
    },
    "LA DORADA":{
        "departamento": ["CALDAS", "CUNDINAMARCA", "BOYACA"], 
        "municipios":["La Dorada", "Manzanares", "Marquetalia", "Pensilvania", "Samaná", "Victoria"]
    },
    "LA GUAJIRA":{
        "departamento": ["LA GUAJIRA"],
        "municipios":[]
    },
    "MAGANGUE":{
        "departamento": ["SUCRE"],
        "municipios":["Magangué", "Achí", "Altos del Rosario", "Barranco de Loba", "Cicuco", "Córdoba", "El Peñón", "Hatillo de Loba", "Margarita", "Mompós", "Montecristo", "Pinillos", "San Fernando", "San Jacinto del Cauca", "San Martín de Loba", "Talaigua Nuevo", "Tiquisio y Zambrano en el departamento de Bolívar y Buenavista, Caimito, Guaranda, Majagual, Sucre"]
    },
    "MAGDALENA MEDIO":{
        "departamento": ["ANTIOQUIA"],
        "municipios":["Puerto Berrío", "Amalfi", "Anorí", "Caracolí", "Cisneros", "El Bagre", "La Magdalena", "Maceo", "Nechí", "Puerto Triunfo", "Puerto Nare", "Remedios", "San Roque", "Segovia", "Vegachí", "Yalí", "Yolombó", "Yondó","Zaragoza"]
    },
    "MEDELLIN PARA ANTIOQUIA":{
        "departamento": ["ANTIOQUIA"],
        "municipios":["Medellín", "Abriaquí", "Amagá", "Andes", "Angelópolis", "Angostura", "Anzá", "Armenia", "Barbosa", "Bello", "Belmira", "Betania", "Betulia", "Briceño", "Buriticá", "Cáceres", "Caicedo", "Campamento", "Caramanta", "Carolina", "Caucasia", "Cañasgordas", "Ciudad Bolívar", "Concordia", "Copacabana", "Don Matías", "Ebéjico", "Entrerríos", "Fredonia", "Frontino", "Giraldo", "Girardota", "Gómez Plata", "Guadalupe" , "Heliconia" , "Hispania" , "Ituango" , "Jardín" , "Jericó" , "La Pintada" , "Liborina" , "Montebello" , "Murindó" , "Olaya" , "Peque" , "Pueblorrico" , "Sabanalarga" , "Salgar" , "San Andrés" , "San Jerónimo" , "San José de la Montaña" , "San Pedro" , "Santa Bárbara" , "Santa Fe de Antioquia" , "Santa Rosa de Osos" , "Santo Domingo" , "Sopetrán" , "Támesis", "Taranza", "Tarso", "Titiribí", "Toledo", "Uramita", "Urrao", "Valdivia", "Valparaíso", "Venecia", "Vigía del Fuerte", "Yarumal"]
    },
    "MONTERIA":{
        "departamento": ["CÓRDOBA"],
        "municipios":[]
    },
    "NEIVA":{
        "departamento": ["HUILA"],
        "municipios":[]
    },
    "OCANA":{
        "departamento": ["NORTE DE SANTANDER"],
        "municipios":["Abrego", "Cachira", "San Calixto", "Hacarí", "El Carmen", "El Tarra", "La Esperanza", "La Playa", "Convención", "Teorama", "Villa Caro"]
    },
    "ORIENTE ANTIOQUENO":{
        "departamento": ["ANTIOQUIA"],
        "municipios":[ "Rionegro", "Abejorral", "Alejandría", "Argelia", "Carmen de Viboral", "Cocorná", "Concepción", "Granada", "Guarne", "Guatapé", "La Ceja", "La Unión", "Marinilla", "Nariño", "El Peñol", "Retiro", "San Carlos", "San Francisco", "San Luis", "San Rafael", "San Vicente", "Santuario","Sonsón"]
    },
    "PALMIRA": {
        "departamento": ["VALLE DEL CAUCA"],
        "municipios":[ "Palmira", "Candelaria", "Florida", "Pradera"]
    },
    "PAMPLONA" :{
        "departamento": ["NORTE DE SANTANDER"],
        "municipios":["Pamplona", "Bochalema", "Cácota", "Chitagá", "Cucutilla", "Labateca", "Mutiscua", "Pamplonita", "Silos", "Toledo"]
    },
    "PASTO": {
        "departamento": ["NARIÑO", "PUTUMAYO"],
        "municipios":["Pasto", "Albán", "Ancuyá", "Arboleda", "Belén", "Buesaco", "Chachagüí", "Colón", "Consacá", "Cumbitara", "El Rosario", "El Tablón", "El Tambo", "Funes", "Guaitarilla", "Imués", "La Cruz", "La Florida", "La Llanada", "La Unión", "Leiva", "Linares", "Los Andes", "Mallama", "Ospina", "Policarpa", "Providencia", "Samaniego", "San Bernardo", "Sandoná", "San Lorenzo", "San Pablo", "San Pedro de Cartago", "Santa Cruz" , 	"Sapuyes" , 	"Taminango" , 	"Tangua" , 	"Túquerres" , 	"Yacuanquer" , 	"Colón" , 	"Sibundoy" , 	"San Francisco" , 	"Santiago"]
    },  
    "PEREIRA": {
        "departamento": ["RISARALDA"],
        "municipios":["Pereira", "Apía", " Balboa", "Belén de Umbría", "Guática", "La Celia", "La Virginia", "Marsella", "Mistrato", "Pueblo Rico", "Quinchía", "Santuario"]
    },
    "PIEDEMONTE ARAUCANO": {
        "departamento": ["ARAUCA", "BOYACA"],
        "municipios":["Saravena", "Arauquita", "Tame", "Fortul", "Cubará"]
    },
    "PUTUMAYO": {
        "departamento": ["PUTUMAYO"],
        "municipios":["Puerto Asís", "La Hormiga", "Mocoa", "Orito", "Puerto Caicedo", "Puerto Guzmán", "Puerto Leguízamo", "San Miguel", "Villa Amazónica", "Villa Garzón"]
    },
    "SAN ANDRES": {
        "departamento": ["SAN ANDRES"],
        "municipios":[]
    },
    "SAN JOSE": {
        "departamento": ["GUAVIARE"],
        "municipios":[]
    },
    "SANTA MARTA PARA EL MAGDALENA": {
        "departamento": ["MAGDALENA"],
        "municipios":["Santa Marta", "Aracataca", "Ariguaní", "Ciénaga", "Chivolo", "El Banco", "El Piñón", "El Retén", "Fundación", "Guamal", "Pijiño del Carmen", "Pivijay", "Plato", "Pueblo Viejo", "Salamina", "San Sebastián de Buenavista", "San Zenón", "Santa Ana", "Tenerife"]
    },
    "SANTA ROSA DE CABAL": {
        "departamento": ["RISARALDA"],
        "municipios":["Santa Rosa de Cabal"]
    },
    "SEVILLA": {
        "departamento": ["VALLE DEL CAUCA"],
        "municipios":["Sevilla", "Caicedonia"]
    },
    "SINCELEJO": {
        "departamento": ["SUCRE"],
        "municipios":["Sincelejo", "Colosó", "Corozal", "Chalán", "Galeras", "La Unión", "Los Palmitos", "Morroa", "Ovejas", "Palmito", "Sampués", "San Benito Abad", "San Juan Betulia", "San Marcos", "San Onofre", "San Pedro", "Sincé", "Tolú", "Toluviejo"]
    },
    "SOACHA":{
        "departamento": ["CUNDINAMARCA"],
        "municipios":["Soacha"]
    },
    "SOGAMOSO": {
        "departamento": ["BOYACA"],
        "municipios":["Sogamoso", "Aquitania", "Betéitiva", "Busbanzá", "Corrales", "Cuítiva", "Firavitoba", "Gámeza", "Iza", "Labranzagrande", "Mongua", "Monguí", "Nobsa", "Pajarito", "Paya", "Pesca", "Pisba", "Tibasosa", "Tópaga", "Tota"]
    },
    "SUR Y ORIENTE DEL TOLIMA": {
        "departamento": ["TOLIMA"],
        "municipios":["Espinal", "Alpujarra", "Ataco", "Carmen de Apicalá", "Coello", "Coyaima", "Cunday", "Chaparral", "Dolores", "Flandes", "Guamo", "Icononzo", "Melgar", "Natagaima", "Ortega", "Planadas", "Prado", "Purificación", "Rioblanco", "Saldaña", "San Luis", "Suárez", "Villarrica"]
    },
    "TULUA":{
        "departamento": ["VALLE DEL CAUCA"],
        "municipios":[ "Tuluá", "Andalucía", "Bugalagrande", "Bolívar", "Riofrío", "Trujillo", "Zarzal"]
    },
    "TUMACO":{
        "departamento": ["NARIÑO"],
        "municipios":["Tumaco", "Barbacoas", "El Charco", "Francisco Pizarro", "La Tola", "Magüí", "Mosquera", "Olaya Herrera", "Santa Bárbara", "Roberto Payán"]
    },
    "TUNJA":{
        "departamento": ["BOYACA"],
        "municipios":["Tunja", "Almeida", "Arcabuco", "Berbeo", "Boyacá", "Briceño", "Buenavista", "Caldas", "Campohermoso", "Chinavita", "Chiquinquirá", "Chíquiza", "Chitaraque", "Ciénega", "Chivatá", "Chivor", "Cómbita", "Coper", "Cucaita", "Gachantivá", "Garagoa", "Guateque", "Guayatá", "Jenesano", "La Capilla", "La Victoria", "Los Cedros", "Macanal", "Maripí", "Miraflores", "Moniquirá", "Motavita", "Muzo", "Nuevo Colón", "Oicatá", "Otanche", "Pachavita", 	"Páez"	,	"Pauna"	,	"Quípama"	,	"Ramiriquí"	,	"Ráquira"	,	"Rondón"	,	"Saboyá"	,	"Sáchica"	,	"Samacá"	,	"San Eduardo"	,	"San José de Pare"	,	"San Luis de Gaceno" , 	"San Miguel de Sema","San Pablo de Borbur","Santa Ana","Santa María","Santa Sofía","Siachoque","Somondoco","Sora","Soracá","Sutamarchán","Sutatenza","Tenza","Tibaná","Tinjacá","Toca","Togüí","Tununguá","Turmequé","Umbita","Ventaquemada","Villa de Leiva","Viracachá","Zetaquirá"]
    },
    "URABA":{
        "departamento": ["ANTIOQUIA"],
        "municipios":["Apartadó", "Arboletes", "Carepa", "Dabeiba", "Chigorodó", "Mutatá", "Necoclí", "San Juan de Urabá", "San Pedro de Urabá", "Turbo"]   
    },
    "VALLEDUPAR":{
        "departamento": ["CESAR"],
        "municipios":["Valledupar", "Agustín Codazzi", "Astrea", "Becerril", "Bosconia", "Chimichagua", "Chiriguaná", "El Copey", "El Paso", "La Jagua de Ibirico", "La Paz", "Manaure", "Balcón del Cesar", "Pueblo Bello", "San Diego"]
    },
    "VILLAVICENCIO":{
        "departamento": ["META", "Vaupés", "Vichada", "Guaviare", "Guainía"],
        "municipios":["Paratebueno"]
    }
}

def normalizarTexto(texto):
    return unicodedata.normalize("NFD", texto)\
        .encode("ascii", "ignore")\
        .decode("utf-8")\
        .upper()
        
def es_resultado_valido(res, camara_info):
    #normalize the test, to avoid issues with accents and case sensitivity
    address = normalizarTexto(res.get("formatted_address", ""))

    # verify if any of the departments or municipalities of the chamber of commerce are in the address
    # if any are, then it is a valid result
    return (
        any(
            normalizarTexto(dep) in address
            for dep in camara_info["departamento"]
        )
        or
        any(
            normalizarTexto(mun) in address
            for mun in camara_info["municipios"]
        )
    )
    
def esta_cerrado(res):
    # returns true if the business is closed temporarily or permanently
    return res.get("business_status") in {
        "CLOSED_TEMPORARILY",
        "CLOSED_PERMANENTLY"
    }

batch_size = 100  # Save results every 100 rows (just in case something happens)
sleep_time = 0.1  # Pause between requests to avoid hitting rate limits


def obtain_coordinates(input_file, temp_file):
    
    # look for existing progress csv
    if os.path.exists(temp_file):
        with open(temp_file, newline='', encoding='utf-8') as f:
            reader = list(csv.DictReader(f))
            start_index = len(reader)
    else:
        start_index = 0

    
    with open(input_file, newline='', encoding='utf-8') as csvfile_in:
        reader = list(csv.DictReader(csvfile_in))

        # new fieldnames for latitud, longitud and direccion
        original_fields = list(reader[0].keys())
        #la direccion se usara para saber si la localizacion es correcta o por lo menos si tiene sentido
        fieldnames = original_fields + ["latitud", "longitud", "direccion"]

        results = []
        if start_index > 0:
            with open(temp_file, newline='', encoding='utf-8') as f:
                results = list(csv.DictReader(f))

        for i in range(start_index, len(reader)):
            row = reader[i]

            # Construct the query
            # just take the name of the store and Colombia as location
            query = f"{row['Nombre']}, Colombia"
            url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={query}&key={apiKey}&language=es"

            try:
                response = requests.get(url)
                data = response.json()

                if data['status'] == 'OK' and len(data['results']) > 0:
                    results_list = data['results']
                    chosen = None
                    
                    # from the list of results_list only we consider those in the correct municipality, if they are not in the correct municipality at least those in the correct department
                    
                    # from formatted address we can get the department and municipality
                    
                    # first take the camara de comercio from row and look in the dictionary of camaras_de_comercio
                    if row['Cámara de Comercio'] in camaras_de_comercio:
                        camara_info = camaras_de_comercio[row['Cámara de Comercio']]
                        
                        # filter results_list for only leaving with the ones in the correct municipality or department
                        results_list = list(
                            filter(
                                lambda res: es_resultado_valido(res, camara_info),
                                results_list
                            )
                        )

                    # if it is cancelled, we prefer closed locations
                    chosen = (
                                next(filter(esta_cerrado, results_list), None)
                                if row['Estado de la matrícula'].strip().upper() == "CANCELADA"
                                else None
                            )

                    # if no closed location found or not cancelled, take the first one
                    if not chosen and results_list:
                        chosen = results_list[0]
                        row['latitud'] = chosen['geometry']['location']['lat']
                        row['longitud'] = chosen['geometry']['location']['lng']
                        row['direccion'] = chosen.get('formatted_address', "")
                    else:
                        row['latitud'] = ""
                        row['longitud'] = ""
                        row['direccion'] = ""
                        
                else:
                    row['latitud'] = ""
                    row['longitud'] = ""
                    row['direccion'] = ""
            except Exception as e:
                print(f"Error en la fila {i}: {e}")
                row['latitud'] = ""
                row['longitud'] = ""
                row['direccion'] = ""

            results.append(row)

            # parcially save every batch_size rows
            if (i + 1) % batch_size == 0 or (i + 1) == len(reader):
                with open(temp_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(results)
                print(f"Guardadas {i + 1} filas de {len(reader)}")

            time.sleep(sleep_time)

    # Reemplace the original file with the temp file
    os.replace(temp_file, input_file)
    print("Proceso terminado. El CSV ahora tiene latitude, longitude y formatted_address.")

print("Iniciando proceso de obtención de coordenadas y direcciones...")
for input_file, temp_file in zip(input_file_list, temp_file_list):
    obtain_coordinates(input_file, temp_file)
print("Todos los archivos han sido procesados.")