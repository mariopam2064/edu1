def substitution(city):
    en_city = ["seoul","anyang","yongin","goyang","chuncheon"]
    ko_city = ['서울','안양','용인','고양','춘천']
    dict = {}
    for i in range(5):
        dict[en_city[i]] = ko_city[i]
    return dict[city]