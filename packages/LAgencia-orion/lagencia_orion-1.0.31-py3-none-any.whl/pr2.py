def main():
    produccion= False

    from orion.journey.journey_villacruz.sends_villacruz import case_1 as case_1_villacruz, case_2 as case_2_villacruz  # noqa: F401
    REAL_ESTATE = "villacruz"
    case_1_villacruz(REAL_ESTATE, produccion)
    case_2_villacruz(REAL_ESTATE, produccion)

    # from orion.journey.journey_castillo.sends_castillo import case_2 as case_2_castillo, case_1 as case_1_castillo # noqa: F401
    # REAL_ESTATE = "castillo"
    # case_1_castillo(REAL_ESTATE, produccion)
    #case_2_castillo(REAL_ESTATE, produccion)

    # from orion.journey.journey_estrella.sends_estrella import case_1 as case_1_estrella, case_2 as case_2_estrella# noqa: F401
    # REAL_ESTATE = "estrella"
    # case_1_estrella(REAL_ESTATE, produccion)
    # case_2_estrella(REAL_ESTATE, produccion)

    # from orion.journey.journey_livin.sends_livin import case_1 as case_1_livin, case_2 as case_2_livin  # noqa: F401
    # REAL_ESTATE = "livin"
    # case_1_livin(REAL_ESTATE, produccion)
    # case_2_livin(REAL_ESTATE, produccion)





if __name__ == "__main__":
    main()
