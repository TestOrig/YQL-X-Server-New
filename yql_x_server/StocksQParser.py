def parseStocksXML(root):
    # This code is from https://github.com/bgant/inkyphat-stockmarket/blob/5f136787311c9831e04edd72d5aae7eb8a4f2863/deprecated/apple_quote.py
    results = {} # Initialize dictionary variable to hold XML response key-value pairs
    symbols = [] # Initialize array variable to hold symbol names
    parts = "" # Initialize string variable to hold parts to send back
    _range = None # Initialize range variable to hold range values
    for child in root.iter(): # Interate through each element in the XML response
        if child.tag == 'symbol':
            symbols.append(child.text)
        if child.tag == 'parts':
            parts = child.text
        if child.tag == 'range':
            _range = child.text
        if child.tag == 'phrase':
            symbols.append(child.text)

    results.update({"symbols": symbols})
    results.update({"parts": parts})
    if _range:
        results.update({"range": _range})
    return results
