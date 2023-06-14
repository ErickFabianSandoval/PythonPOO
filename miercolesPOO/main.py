from cosas import Alumno, Perro

def main():
    al1 = Alumno("Jose", 19, "ICO")
    print(vars(al1))

    al1.set_nombre("María")
    print(vars(al1))
    print("-------------------")
    print(al1) #este es el to string
    al1.estudiar(5)
    print("----------------")
    perro1 = Perro("Poodle",2, 0.35)
    print(vars(perro1))
    perro1.raza = "De la calle"#Set en notacion pythonic
    print(vars(perro1))
    print(perro1)
    cachorro = Perro.es_cachorro(perro1.edad)
    print(cachorro)
    Perro.dormir()
    danes = Perro.perro_grande(0.8)
    print(danes)


main()


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
