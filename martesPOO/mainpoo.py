from cosas import Alumno

def main():
    """
    al1 = Alumno()
    print(al1)
    al2 = Alumno()
    print(al1.facultad)
    print(al2.facultad)
    print(Alumno.facultad)
    #OJO
    print("--------")
    al1.facultad = "Fes aragon EDOmex"#Se agrega un atributo
    print(al1.facultad)
    print(al2.facultad)
    print(Alumno.facultad)
    print("Un vistazo a los objetos")
    print(vars(al1))
    print(vars(al2))
    print("---MOdificar atributos públicos---")
    al1.edad = 999 #No hay encapsulamiento
    """
    al1 = Alumno("Diego", 19, "Economia")
    al2 = Alumno("Monse", 18, "Derecho")
    

main()