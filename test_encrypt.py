from nacl.public import PrivateKey, PublicKey, Box
message = b'Testing message'

# Create rambo keys
rambokey = PrivateKey.generate()
with open('keys/rambo_key','wb') as f: f.write(rambokey.encode())
with open('keys/rambo_key.pub','wb') as f: f.write(rambokey.public_key.encode())

# Create client keys
clientkey = PrivateKey.generate()
with open('keys/client_key.pub','wb') as f: f.write(clientkey.public_key.encode())

# Encrypt message
with open('keys/rambo_key.pub', 'rb') as f: rambokey_pub = PublicKey(f.read())
client_box = Box(clientkey, rambokey_pub)
encrypted_message = client_box.encrypt(message)

# Save message
with open('test_message', 'wb') as f: f.write(encrypted_message)

# Read keys and message from files
with open('keys/rambo_key', 'rb') as f: rambokey2 = PrivateKey(f.read())
with open('keys/client_key.pub', 'rb') as f: clientkey_pub = PublicKey(f.read())
with open('test_message', 'rb') as f: message_read = f.read()

# Decrypt
rambo_box = Box(rambokey2, clientkey_pub)
message_dec = rambo_box.decrypt(message_read)

print(message_dec)
