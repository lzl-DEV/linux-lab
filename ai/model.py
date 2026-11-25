#!/usr/bin/env python3
import torch.nn as nn  # 导入 PyTorch 神经网络模块

# 定义一个继承自 nn.Module 的神经网络类
class NeuralNetwork(nn.Module):
    def __init__(self):
        super().__init__()  # 调用父类 nn.Module 的构造函数
        # 第一层卷积层：输入 1 通道灰度图，输出 32 个特征图，卷积核 3x3，步长 1
        self.conv1 = nn.Conv2d(1, 32, 3, 1)
        # 第二层卷积层：输入 32 通道，输出 64 个特征图
        self.conv2 = nn.Conv2d(32, 64, 3, 1)
        # 第一个全连接层：两次卷积+两次池化后特征图为 64*5*5=1600
        self.fc1 = nn.Linear(in_features=64 * 5 * 5, out_features=128)
        # 第二个全连接层（输出层）：10 个类别对应 0-9
        self.fc2 = nn.Linear(in_features=128, out_features=10)

    def forward(self, x):
        # (N,1,28,28) -> Conv1 -> (N,32,26,26) -> ReLU
        x = nn.functional.relu(self.conv1(x))
        # (N,32,26,26) -> MaxPool -> (N,32,13,13)
        x = nn.functional.max_pool2d(x, kernel_size=2)
        # (N,32,13,13) -> Conv2 -> (N,64,11,11) -> ReLU
        x = nn.functional.relu(self.conv2(x))
        # (N,64,11,11) -> MaxPool -> (N,64,5,5)
        x = nn.functional.max_pool2d(x, kernel_size=2)
        # 展平：(N,64,5,5) -> (N,1600)
        x = x.view(-1, 64 * 5 * 5)
        # (N,1600) -> FC1 -> (N,128) -> ReLU
        x = nn.functional.relu(self.fc1(x))
        # (N,128) -> FC2 -> (N,10)，交叉熵损失内部含 Softmax，这里不再加
        x = self.fc2(x)
        return x
