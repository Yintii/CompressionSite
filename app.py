from flask import Flask, request, render_template, send_file
from collections import Counter
import io, heapq, pickle

app = Flask(__name__)


class HuffmanNode:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq


def build_huffman_tree(text):
    frequency = Counter(text)
    heap = [HuffmanNode(char, freq) for char, freq in frequency.items()]
    heapq.heapify(heap)

    while len(heap) > 1:
        node1 = heapq.heappop(heap)
        node2 = heapq.heappop(heap)
        merged = HuffmanNode(None, node1.freq + node2.freq)
        merged.left = node1
        merged.right = node2
        heapq.heappush(heap, merged)

    return heap[0]


def build_codes(node, prefix='', codebook=None):
    if codebook is None:
        codebook = {}
    if node.char is not None:
        codebook[node.char] = prefix
    else:
        if node.left:
            build_codes(node.left, prefix + '0', codebook)
        if node.right:
            build_codes(node.right, prefix + '1', codebook)
    return codebook


def huffman_compress(text):
    root = build_huffman_tree(text)
    huffman_codes = build_codes(root)
    compressed = ''.join(huffman_codes[char] for char in text)
    return compressed, huffman_codes


def pad_encoded_text(encoded_text):
    extra_padding = 8 - len(encoded_text) % 8
    for _ in range(extra_padding):
        encoded_text += "0"

    padded_info = "{0:08b}".format(extra_padding)
    encoded_text = padded_info + encoded_text
    return encoded_text


def get_byte_array(padded_encoded_text):
    if len(padded_encoded_text) % 8 != 0:
        print("Encoded text not padded properly")
        exit(0)

    byte_array = bytearray()
    for i in range(0, len(padded_encoded_text), 8):
        byte = padded_encoded_text[i:i + 8]
        byte_array.append(int(byte, 2))
    return byte_array


def huffman_decompress(padded_encoded_text, huffman_codes):
    padded_info = padded_encoded_text[:8]
    extra_padding = int(padded_info, 2)

    encoded_text = padded_encoded_text[8:]  # remove padding info
    encoded_text = encoded_text[:-1 * extra_padding]  # remove extra padding

    reverse_codes = {v: k for k, v in huffman_codes.items()}
    current_code = ''
    decompressed = []

    for bit in encoded_text:
        current_code += bit
        if current_code in reverse_codes:
            decompressed.append(reverse_codes[current_code])
            current_code = ''

    return ''.join(decompressed)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/compress', methods=['POST'])
def compress():
    file = request.files['file']
    data = file.read().decode('utf-8')
    compressed_data, huffman_codes = huffman_compress(data)

    # Pad the encoded text
    padded_encoded_text = pad_encoded_text(compressed_data)
    byte_array = get_byte_array(padded_encoded_text)

    # Serialize the Huffman codes
    huffman_codes_bytes = pickle.dumps(huffman_codes)

    # Write the compressed data and Huffman codes to the output file
    output = io.BytesIO()
    output.write(huffman_codes_bytes)
    output.write(byte_array)
    output.seek(0)

    return send_file(output, download_name='compressed.bin', as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
