import ssl

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain("certificate.pem", "privateKey.pem")

print("TLS Loaded!!")