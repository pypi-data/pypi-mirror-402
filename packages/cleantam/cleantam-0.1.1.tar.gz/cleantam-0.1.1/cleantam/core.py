import pandas as pd
import unicodedata

@pd.api.extensions.register_dataframe_accessor("latam")
class LatamAccessor:
    def __init__(self, pandas_obj):
        self._obj = pandas_obj

    def a_float(self, columnas):
        """
        Convierte columnas con formato latino (1.500,50) a float (1500.50).
        Acepta una columna (str) o lista de columnas.
        """
        if isinstance(columnas, str):
            columnas = [columnas]
            
        for col in columnas:
            # Eliminar puntos de mil, cambiar coma decimal por punto
            self._obj[col] = (self._obj[col]
                              .astype(str)
                              .str.replace('.', '', regex=False)
                              .str.replace(',', '.', regex=False)
                              # Limpiar símbolos de moneda si los hay
                              .str.replace('$', '', regex=False)
                              .str.strip())
            
            self._obj[col] = pd.to_numeric(self._obj[col], errors='coerce')
        
        return self._obj

    def normalizar_texto(self, columnas):
        """
        Quita tildes, pasa a minúsculas y elimina espacios extra.
        """
        if isinstance(columnas, str):
            columnas = [columnas]

        def _quitar_tildes(texto):
            if not isinstance(texto, str): return texto
            texto = unicodedata.normalize('NFD', texto)
            return texto.encode('ascii', 'ignore').decode("utf-8")

        for col in columnas:
            # Aplicar limpieza
            self._obj[col] = (self._obj[col]
                              .astype(str)
                              .str.lower()
                              .str.strip()
                              .apply(_quitar_tildes))
        return self._obj

    def limpiar_headers(self):
        """
        Estandariza los nombres de las columnas:
        'Fecha de Nacimiento' -> 'fecha_de_nacimiento'
        """
        self._obj.columns = (self._obj.columns
                             .str.strip()
                             .str.lower()
                             .str.replace(' ', '_')
                             .str.replace(r'[áéíóú]', '', regex=True))
        return self._obj