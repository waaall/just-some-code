# train_gpu_test.py
import torch
import torch.nn as nn
import torch.optim as optim
import logging
import time
from pathlib import Path

logger = logging.getLogger("GPUModuleTester")

class GPUModuleTester:
    def __init__(self, N=40960, D_in=2048, H=1024, D_out=100, epochs=1000, lr=1e-3,
                 log_file: str = "train.log"):
        # --- Logger 设置 ---
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        logger.setLevel(logging.INFO)

        # 控制台输出
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        # 文件输出
        fh = logging.FileHandler(log_file, mode="w")
        fh.setLevel(logging.INFO)

        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)

        # 避免重复添加 handler
        if not logger.handlers:
            logger.addHandler(ch)
            logger.addHandler(fh)

        # --- 设备选择 ---
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")

        # 随机数据
        self.x = torch.randn(N, D_in, device=self.device)
        self.y = torch.randint(0, D_out, (N,), device=self.device)

        # 模型
        self.model = nn.Sequential(
            nn.Linear(D_in, H),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(H, H),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(H, H // 2),
            nn.ReLU(),
            nn.Linear(H // 2, D_out),
        ).to(self.device)

        self.loss_fn = nn.CrossEntropyLoss()
        self.optimizer = optim.Adam(self.model.parameters(), lr=lr)
        self.epochs = epochs

    def train(self):
        logger.info(f"Starting training for {self.epochs} epochs...")
        start_time = time.time()
        
        for epoch in range(self.epochs):
            epoch_start = time.time()
            
            self.optimizer.zero_grad()
            y_pred = self.model(self.x)
            loss = self.loss_fn(y_pred, self.y)
            loss.backward()
            self.optimizer.step()

            epoch_time = time.time() - epoch_start
            
            if epoch % 50 == 0:
                elapsed_time = time.time() - start_time
                eta = (elapsed_time / (epoch + 1)) * (self.epochs - epoch - 1)
                logger.info(f"Epoch {epoch}/{self.epochs}, Loss: {loss.item():.4f}, "
                           f"Epoch Time: {epoch_time:.3f}s, Elapsed: {elapsed_time:.1f}s, "
                           f"ETA: {eta:.1f}s")

        total_time = time.time() - start_time
        avg_epoch_time = total_time / self.epochs
        logger.info(f"Training finished! Total time: {total_time:.2f}s, "
                   f"Average per epoch: {avg_epoch_time:.3f}s")


def main():
    tester = GPUModuleTester()
    tester.train()


if __name__ == "__main__":
    main()