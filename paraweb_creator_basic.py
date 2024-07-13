import argparse
from PIL import Image
import numpy as np
import rsa


def read_message_from_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except IOError as e:
        print(f"Could not read file: {e}")
        exit(1)


def enhanced_encode_message(image_path, messages, output_path, delim=None, message_file=None, encrypt_rsa=""):
    # If a message file is provided, override the message with the file's content
    if message_file:
        messages = read_message_from_file(message_file)

    if type(messages) == str:
        if delim:
            messages = messages.split(delim)
        else:
            messages = [messages, '', '']
    if not hasattr(messages, "__len__"):
        print(f"Error: message is of invalid data type: {messages}")
        return
    elif len(messages) < 3:
        print(f"Error: message length less than 3: {len(messages)}")
        return

    if encrypt_rsa:
        with open(encrypt_rsa, 'rb+') as public_file:
            public_key = rsa.PublicKey.load_pkcs1(public_file.read(), format='PEM')
        for i in range(len(messages)):
            print(f"""Original: {messages[i]}, Result: {rsa.encrypt(messages[i], public_key)}""")
            messages[i] = rsa.encrypt(messages[i], public_key)

    img = Image.open(image_path)
    encoded = img.copy()
    pixels = np.array(encoded)

    for channel in range(len(messages)):
        # skip if null or empty message is provided for this channel
        if not messages[channel]:
            continue

        # Convert message to binary using UTF-8 encoding
        message_bytes = messages[channel].encode('utf-8')  # Encode the message as bytes using UTF-8
        message_bits = ''.join([bin(byte)[2:].rjust(8, '0') for byte in message_bytes])

        # Include the length of the message as a 32-bit binary at the beginning
        message_length = len(message_bits)
        length_bits = bin(message_length)[2:].rjust(32, '0')

        # Error correction: Repeat each bit twice
        message_bits = length_bits + ''.join(bit * 2 for bit in message_bits)

        if len(message_bits) > (pixels.shape[0] * pixels.shape[1] * 2 - 32):
            raise ValueError("The image is too small to hold this message.")

        data_index = 0
        for row in range(pixels.shape[0]):
            for col in range(pixels.shape[1]):
                if data_index < len(message_bits):
                    # Store two bits in corresponding RGB channel
                    bits_to_store = message_bits[data_index:data_index+2] if data_index + 1 < len(message_bits) else message_bits[-1] + '0'
                    pixels[row, col, channel] &= 0b11111100  # Clear the last two bits
                    pixels[row, col, channel] |= int(bits_to_store, 2)  # Set the last two bits
                    data_index += 2
                else:
                    break
            if data_index >= len(message_bits):
                break

    # Save the modified image
    encoded = Image.fromarray(pixels)
    encoded.save(output_path)


def main():
    parser = argparse.ArgumentParser(description='Encode a message or the contents of a file into an image using steganography.')
    parser.add_argument('image_path', type=str, help='Path to the input image file')
    parser.add_argument('--message', type=str, default='', help='The message to encode into the image. Ignored if --message-file is provided.')
    parser.add_argument('--message-file', type=str, help='Path to a text or HTML file containing the message to encode. Overrides --message.')
    parser.add_argument('output_path', type=str, help='Path to save the encoded image')
    parser.add_argument('--d', type=str, help='Delimeter used to separate the input message into messages for channel. Messages are placed in order of entry into R, G, B.')
    parser.add_argument('--encrypt_rsa', type=str, help='Encrypt with RSA using public key in input file path.')
    
    args = parser.parse_args()

    # Validate that either a message or a message file is provided
    if not args.message and not args.message_file:
        parser.error('No message provided. Use --message to specify a message or --message-file to specify a file containing the message.')

    try:
        enhanced_encode_message(args.image_path, args.message, args.output_path, args.d, args.message_file, args.encrypt_rsa)
        print(f"Message successfully encoded and saved to {args.output_path}")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == '__main__':
    main()
    