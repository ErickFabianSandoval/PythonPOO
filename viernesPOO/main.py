from cosas import *

def main():

    per1 = Persona("Jose",19)
    print(per1)
    print(Persona.descripcion)

    print("------herencia alumno-----")
    al1 = Alumno("Jose", 19, "3203910", "ICO")
    print(al1)
    print(Alumno.descripcion)

    al2 = Alumno.constructor_defecto()
    print(al2)
    al2.nombre = "Juan"
    print(al2)
    al2.dormir()

    print("-----Herencia profe------")
    profe1 = Profesor("jesus",30+16, 363589, "Ingenieria de Software")
    print(profe1)
    profe1.dormir()

    print("-------herencia ayudante profe----")
    ayudante = AyudanteProfesor("Adrian", 20, "25362","ICO", 23243, "Ing. de Software",4 )
    print(ayudante)
    ayudante.dormir()
    ayudante.nombre = "Abraham"
    ayudante.dar_clase("P.O.O.")

main()

