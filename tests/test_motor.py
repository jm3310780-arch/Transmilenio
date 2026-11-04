"""Pruebas del motor con una red pequeña hecha a mano.

Uso: python -m unittest discover tests
"""

import os
import tempfile
import unittest

from motor import Red, simular_fila

ESTACIONES = ["A", "B", "C", "D", "E", "CALLE 26", "CALLE 45", "CALLE 80", "CAN"]
RUTAS = {
    "R1": ["A", "B", "C", "D"],
    "R2": ["C", "E"],
    "R3": ["CALLE 26", "CALLE 45", "CALLE 80"],
}
HORARIOS = [
    ("R1", "A", "06:00"), ("R1", "A", "05:30"), ("R1", "A", "07:15"),
    ("R1", "B", "06:05"), ("R1", "C", "06:10"), ("R1", "D", "06:20"),
    ("R2", "C", "06:30"), ("R2", "C", "06:40"), ("R2", "E", "06:50"),
]


def crear_red():
    carpeta = tempfile.mkdtemp()
    with open(os.path.join(carpeta, "estaciones.csv"), "w") as f:
        f.write("nombre\n" + "\n".join(ESTACIONES) + "\n")
    with open(os.path.join(carpeta, "rutas.csv"), "w") as f:
        f.write("ruta,orden,estacion\n")
        for ruta, paradas in RUTAS.items():
            # Se escriben al revés para probar que se ordena por "orden".
            for i in range(len(paradas) - 1, -1, -1):
                f.write(f"{ruta},{i + 1},{paradas[i]}\n")
    with open(os.path.join(carpeta, "horarios.csv"), "w") as f:
        f.write("ruta,estacion,hora\n")
        for fila in HORARIOS:
            f.write(",".join(fila) + "\n")
    return Red(carpeta)


class PruebasMotor(unittest.TestCase):
    def setUp(self):
        self.red = crear_red()

    def test_r1_estado(self):
        self.assertEqual(self.red.estado("A"), (True, True))
        self.assertEqual(self.red.estado("Z"), (False, False))
        self.red.cerrar("A")
        self.assertEqual(self.red.estado("A"), (True, False))

    def test_r2_autocompletar(self):
        self.assertEqual(self.red.autocompletar("CA", 10),
                         ["CALLE 26", "CALLE 45", "CALLE 80", "CAN"])
        self.assertEqual(self.red.autocompletar("CA", 2), ["CALLE 26", "CALLE 45"])
        self.assertEqual(self.red.autocompletar("X", 3), [])
        self.assertEqual(self.red.autocompletar("CA", 0), [])
        self.red.cerrar("CALLE 45")
        self.assertEqual(self.red.autocompletar("CALLE", 5), ["CALLE 26", "CALLE 80"])

    def test_r3_rango(self):
        self.assertEqual(self.red.rango("CALLE 26", "CALLE 80"),
                         ["CALLE 26", "CALLE 45", "CALLE 80"])
        self.assertEqual(self.red.rango("B", "D"), ["B", "C", "CALLE 26", "CALLE 45",
                                                    "CALLE 80", "CAN", "D"])
        self.assertEqual(self.red.rango("Z", "A"), [])
        self.red.cerrar("C")
        self.assertEqual(self.red.rango("B", "C"), ["B"])

    def test_r4_proximo_bus(self):
        self.assertEqual(self.red.proximo_bus("A", "R1", "05:00"), "05:30")
        self.assertEqual(self.red.proximo_bus("A", "R1", "06:00"), "06:00")
        self.assertEqual(self.red.proximo_bus("A", "R1", "06:01"), "07:15")
        self.assertIsNone(self.red.proximo_bus("A", "R1", "08:00"))
        self.assertIsNone(self.red.proximo_bus("E", "R1", "05:00"))
        self.assertIsNone(self.red.proximo_bus("A", "NO", "05:00"))
        self.red.cerrar("A")
        self.assertIsNone(self.red.proximo_bus("A", "R1", "05:00"))

    def test_r5_viaje(self):
        self.assertEqual(self.red.viaje("A", "C"), [("R1", "A", "C", 2)])
        self.assertEqual(self.red.viaje("A", "E"),
                         [("R1", "A", "C", 2), ("R2", "C", "E", 1)])
        self.assertIsNone(self.red.viaje("D", "A"))  # las rutas van en un sentido
        self.assertIsNone(self.red.viaje("A", "CALLE 80"))
        self.assertEqual(self.red.viaje("A", "A"), [])
        self.red.cerrar("C")  # no se puede transbordar en una cerrada
        self.assertIsNone(self.red.viaje("A", "E"))
        self.assertEqual(self.red.viaje("A", "D"), [("R1", "A", "D", 3)])

    def test_r6_ranking(self):
        self.assertEqual(self.red.ranking(2), [("A", 3), ("C", 3)])
        self.red.cerrar("A")
        self.assertEqual(self.red.ranking(1), [("C", 3)])
        self.red.quitar_parada("R2", "C")
        self.assertEqual(self.red.ranking(2), [("B", 1), ("C", 1)])

    def test_r7_editar_rutas(self):
        self.assertTrue(self.red.agregar_parada("R1", "E", "B"))
        self.assertEqual(self.red.recorrido("R1"), ["A", "B", "E", "C", "D"])
        self.assertEqual(self.red.recorrido("R1", al_reves=True), ["D", "C", "E", "B", "A"])
        self.assertFalse(self.red.agregar_parada("R1", "E", "A"))   # ya está
        self.assertFalse(self.red.agregar_parada("R1", "Z", "A"))   # no existe
        self.assertFalse(self.red.agregar_parada("R1", "CAN", "Z"))
        self.assertTrue(self.red.agregar_parada("R1", "CAN", None))
        self.assertEqual(self.red.recorrido("R1")[0], "CAN")
        self.assertTrue(self.red.quitar_parada("R1", "D"))
        self.assertFalse(self.red.quitar_parada("R1", "D"))
        self.assertEqual(self.red.recorrido("R1"), ["CAN", "A", "B", "E", "C"])
        self.assertEqual(self.red.recorrido("NO"), [])

    def test_r8_cerrar_reabrir(self):
        self.assertTrue(self.red.cerrar("B"))
        self.assertFalse(self.red.cerrar("B"))
        self.assertFalse(self.red.cerrar("Z"))
        self.assertTrue(self.red.reabrir("B"))
        self.assertFalse(self.red.reabrir("B"))

    def test_r9_deshacer_rehacer(self):
        self.assertFalse(self.red.deshacer())
        self.red.cerrar("A")
        self.red.quitar_parada("R1", "B")
        self.red.agregar_parada("R2", "D", None)
        self.assertTrue(self.red.deshacer())
        self.assertEqual(self.red.recorrido("R2"), ["C", "E"])
        self.assertTrue(self.red.deshacer())
        self.assertEqual(self.red.recorrido("R1"), ["A", "B", "C", "D"])
        self.assertTrue(self.red.deshacer())
        self.assertEqual(self.red.estado("A"), (True, True))
        self.assertFalse(self.red.deshacer())
        self.assertTrue(self.red.rehacer())
        self.assertEqual(self.red.estado("A"), (True, False))
        # Un cambio nuevo borra lo que había para rehacer.
        self.red.cerrar("C")
        self.assertFalse(self.red.rehacer())
        self.assertTrue(self.red.deshacer())
        self.assertTrue(self.red.rehacer())
        self.assertEqual(self.red.estado("C"), (True, False))

    def test_r10_fila(self):
        self.assertEqual(simular_fila([0, 0, 1, 2, 3, 10, 11], 5, 2),
                         [0, 0, 5, 5, 10, 10, 15])
        self.assertEqual(simular_fila([], 5, 2), [])
        self.assertEqual(simular_fila([7, 1], 5, 10), [5, 10])  # desordenadas
        with self.assertRaises(ValueError):
            simular_fila([1], 0, 1)

    def test_datos_reales(self):
        carpeta = os.path.join(os.path.dirname(__file__), "..", "datos")
        red = Red(carpeta)
        self.assertEqual(red.estado("PORTAL NORTE"), (True, True))
        self.assertIsNotNone(red.viaje("PORTAL NORTE", "PORTAL SUR"))


if __name__ == "__main__":
    unittest.main()
