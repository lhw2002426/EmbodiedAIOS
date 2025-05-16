# wheatfox
# 将点云文件去除颜色，测试用

import open3d as o3d
import argparse

# -i {input_ply}
# -o default is the same file with _converted suffix

# pcd = o3d.io.read_point_cloud("colored_point_cloud.ply")
# pcd.colors = o3d.utility.Vector3dVector([[0, 0, 0] for _ in range(len(pcd.points))])
# o3d.io.write_point_cloud("lidar_simulated_point_cloud.ply", pcd)


def convert_ply(input_file, output_file=None):
    pcd = o3d.io.read_point_cloud(input_file)

    pcd.colors = o3d.utility.Vector3dVector(
        [[0, 0, 0] for _ in range(len(pcd.points))])

    if output_file is None:
        output_file = input_file.replace(".ply", "_converted.ply")
    o3d.io.write_point_cloud(output_file, pcd)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert PLY file to black point cloud.")
    parser.add_argument("-i", "--input", type=str,
                        required=True, help="Input PLY file path")
    parser.add_argument("-o", "--output", type=str,
                        help="Output PLY file path (default: input file with '_converted' suffix)")
    args = parser.parse_args()

    convert_ply(args.input, args.output)
