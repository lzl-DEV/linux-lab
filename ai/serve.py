#!/usr/bin/env python3
import base64
from io import BytesIO

import torch
from PIL import Image, ImageOps
from flask import Flask, request, redirect, jsonify
from torchvision import transforms

from model import NeuralNetwork

device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f'using {device}')
model = NeuralNetwork().to(device)
path = './mnist.pth'
model.load_state_dict(torch.load(path))
print(f'loaded model from {path}')
print(model)

app = Flask(__name__)


@app.route('/')
def index():
    return redirect('/static/index.html')


@app.route('/api', methods=['POST'])
def api():
    data = request.get_json()
    image_data = base64.b64decode(data['image'])
    image = Image.open(BytesIO(image_data)).convert('L').resize((28, 28))
    image = ImageOps.invert(image)  # 画布是白底黑字，需转成 MNIST 的黑底白字
    trans = transforms.Compose([
        transforms.Grayscale(1),
        transforms.ToTensor()
    ])
    image_tensor = trans(image).unsqueeze(0).to(device)
    model.eval()
    with torch.no_grad():
        output = model(image_tensor)
        probs = torch.nn.functional.softmax(output[0], 0)
    predict = torch.argmax(probs).item()
    prob = probs[predict]
    print(f'predict: {predict}, prob: {prob}')
    return jsonify({
        'result': predict,
        'probability': prob.item()
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
