# Spatiallm 配置和使用

## 配置环境

（1）确保有一个可用的 NVIDIA 显卡，并安装了 CUDA 12 版本和 cuDNN，具体安装方法可以参考[NVIDIA 官网](https://docs.nvidia.com/cuda/cuda-installation-guide-linux/)。

（2）在目录运行：

```bash
conda create -n spatiallm python=3.11
conda activate spatiallm
conda install -y nvidia/label/cuda-12.4.0::cuda-toolkit conda-forge::sparsehash
pip install poetry && poetry config virtualenvs.create false --local
poetry install
poe install-torchsparse 
```

注意事项：请务必在安装 CUDA 之后，再进行 poe install-torchsparse 的安装，因为涉及到链接 CUDA 库的操作，如果先安装 poe install-torchsparse ，再安装 CUDA ，会发生链接错误！

注意事项：上面的这些操作可能会相当耗时，请耐心等待，尤其是最后的编译。

## 运行模型

（1）下载一个测试点云：

```bash
huggingface-cli download manycore-research/SpatialLM-Testset pcd/scene0000_00.ply --repo-type dataset --local-dir .
```

（2）运行模型：

```bash
python inference.py --point_cloud pcd/scene0000_00.ply --output scene0000_00.txt --model_path manycore-research/SpatialLM-Llama-1B
```

（3）可视化结果：

```bash
python visualize.py --point_cloud pcd/scene0000_00.ply --layout scene0000_00.txt --save scene0000_00.rrd
rerun scene0000_00.rrd # 前面应该已经自动装好rerun了，但是请在桌面环境运行，在SSH运行则会无法启动display
```

## 输入与输出

目前模型能够输入一个 `ply` 格式的 3D 模型文件（点云），经测试可以不带颜色。经过前面的 inference.py 运行后，会生成一个 `scene0000_00.txt` 的文件（名字可以通过 --output 修改），这个文件就是模型的输出，里面记录了每个点云的语义分割结果：

```txt
wall_0=Wall(2.0243586778640745,-6.5632024765014645,0.026850323379039767,5.2743586778640745,-6.5632024765014645,0.026850323379039767,2.68,0.0)
wall_1=Wall(2.0243586778640745,-6.5632024765014645,0.026850323379039767,2.0243586778640745,-1.6132024765014652,0.026850323379039767,2.68,0.0)
wall_2=Wall(5.2743586778640745,-6.5632024765014645,0.026850323379039767,5.2743586778640745,-1.6132024765014652,0.026850323379039767,2.68,0.0)
wall_3=Wall(2.0243586778640745,-1.6132024765014652,0.026850323379039767,5.2743586778640745,-1.6132024765014652,0.026850323379039767,2.68,0.0)
window_0=Window(wall_0,3.674358677864075,-6.5632024765014645,1.5268503233790398,3.2,1.72)
bbox_0=Bbox(bed,4.174358677864075,-4.463202476501465,0.4268503233790398,-1.5708000000000002,1.8125,2.21875,0.8125)
bbox_1=Bbox(stool,4.874358677864075,-5.713202476501465,0.22685032337903976,-1.5708000000000002,0.375,0.375,0.375)
bbox_2=Bbox(nightstand,5.0243586778640745,-3.2632024765014647,0.27685032337903975,-1.5708000000000002,0.53125,0.40625,0.46875)
bbox_3=Bbox(wardrobe,4.474358677864075,-2.663202476501465,1.2268503233790398,-3.1416,1.5625,0.53125,2.375)
bbox_4=Bbox(curtain,3.674358677864075,-6.513202476501465,1.5768503233790399,-3.1416,3.1875,0.125,1.9375)
```

其中主要分为：wall、windows、door和box，其中box里面的标签表示推理出来的这个“box”可能的语义对象，比如 bed、wardrobe、curtain等，其中box运行的结果不是很稳定，每次结果都不一样，墙体和窗户的识别结果相对稳定。

数据字段的含义如下：

```python
@dataclass
class Wall:
    ax: int
    ay: int
    az: int
    bx: int
    by: int
    bz: int
    height: int
    thickness: int

@dataclass
class Door:
    wall_id: str
    position_x: int
    position_y: int
    position_z: int
    width: int
    height: int

@dataclass
class Window:
    wall_id: str
    position_x: int
    position_y: int
    position_z: int
    width: int
    height: int

@dataclass
class Bbox:
    class: str
    position_x: int
    position_y: int
    position_z: int
    angle_z: int
    scale_x: int
    scale_y: int
    scale_z: int
```

## 从 RGB 视频中生成点云并运行 spatiallm

请参考 [EXAMPLE.md](./EXAMPLE.md) 中的内容。

https://github.com/PKU-VCL-3DV/SLAM3R