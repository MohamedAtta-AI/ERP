"""
Convert MiniFASNetV2 PyTorch checkpoint (.pth) to ONNX format.

This script loads the 2.7_80x80_MiniFASNetV2.pth model from the 
Silent-Face-Anti-Spoofing repo and exports it to ONNX.

Architecture is copied from:
https://github.com/minivision-ai/Silent-Face-Anti-Spoofing/blob/master/src/model_lib/MiniFASNet.py

Requirements:
    pip install torch onnx

Usage:
    python scripts/convert_pth_to_onnx.py
"""

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = REPO_ROOT / "models"

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
except ImportError:
    print("ERROR: PyTorch is required for conversion.")
    print("Install with: pip install torch")
    sys.exit(1)


# =====================================================================
# Architecture from Silent-Face-Anti-Spoofing (exact copy)
# =====================================================================

class Flatten(nn.Module):
    def forward(self, input):
        return input.view(input.size(0), -1)


class Conv_block(nn.Module):
    def __init__(self, in_c, out_c, kernel=(1, 1), stride=(1, 1), padding=(0, 0), groups=1):
        super(Conv_block, self).__init__()
        self.conv = nn.Conv2d(in_c, out_c, kernel_size=kernel, groups=groups, stride=stride, padding=padding, bias=False)
        self.bn = nn.BatchNorm2d(out_c)
        self.prelu = nn.PReLU(out_c)

    def forward(self, x):
        x = self.conv(x)
        x = self.bn(x)
        x = self.prelu(x)
        return x


class Linear_block(nn.Module):
    def __init__(self, in_c, out_c, kernel=(1, 1), stride=(1, 1), padding=(0, 0), groups=1):
        super(Linear_block, self).__init__()
        self.conv = nn.Conv2d(in_c, out_channels=out_c, kernel_size=kernel, groups=groups, stride=stride, padding=padding, bias=False)
        self.bn = nn.BatchNorm2d(out_c)

    def forward(self, x):
        x = self.conv(x)
        x = self.bn(x)
        return x


class Depth_Wise(nn.Module):
    def __init__(self, c1, c2, c3, residual=False, kernel=(3, 3), stride=(2, 2), padding=(1, 1), groups=1):
        super(Depth_Wise, self).__init__()
        c1_in, c1_out = c1
        c2_in, c2_out = c2
        c3_in, c3_out = c3
        self.conv = Conv_block(c1_in, out_c=c1_out, kernel=(1, 1), padding=(0, 0), stride=(1, 1))
        self.conv_dw = Conv_block(c2_in, c2_out, groups=c2_in, kernel=kernel, padding=padding, stride=stride)
        self.project = Linear_block(c3_in, c3_out, kernel=(1, 1), padding=(0, 0), stride=(1, 1))
        self.residual = residual

    def forward(self, x):
        if self.residual:
            short_cut = x
        x = self.conv(x)
        x = self.conv_dw(x)
        x = self.project(x)
        if self.residual:
            output = short_cut + x
        else:
            output = x
        return output


class Residual(nn.Module):
    def __init__(self, c1, c2, c3, num_block, groups, kernel=(3, 3), stride=(1, 1), padding=(1, 1)):
        super(Residual, self).__init__()
        modules = []
        for i in range(num_block):
            c1_tuple = c1[i]
            c2_tuple = c2[i]
            c3_tuple = c3[i]
            modules.append(Depth_Wise(c1_tuple, c2_tuple, c3_tuple, residual=True, kernel=kernel, padding=padding, stride=stride, groups=groups))
        self.model = nn.Sequential(*modules)

    def forward(self, x):
        return self.model(x)


class MiniFASNet(nn.Module):
    def __init__(self, keep, embedding_size, conv6_kernel=(7, 7), drop_p=0.0, num_classes=3, img_channel=3):
        super(MiniFASNet, self).__init__()
        self.embedding_size = embedding_size

        self.conv1 = Conv_block(img_channel, keep[0], kernel=(3, 3), stride=(2, 2), padding=(1, 1))
        self.conv2_dw = Conv_block(keep[0], keep[1], kernel=(3, 3), stride=(1, 1), padding=(1, 1), groups=keep[1])

        c1 = [(keep[1], keep[2])]
        c2 = [(keep[2], keep[3])]
        c3 = [(keep[3], keep[4])]
        self.conv_23 = Depth_Wise(c1[0], c2[0], c3[0], kernel=(3, 3), stride=(2, 2), padding=(1, 1), groups=keep[3])

        c1 = [(keep[4], keep[5]), (keep[7], keep[8]), (keep[10], keep[11]), (keep[13], keep[14])]
        c2 = [(keep[5], keep[6]), (keep[8], keep[9]), (keep[11], keep[12]), (keep[14], keep[15])]
        c3 = [(keep[6], keep[7]), (keep[9], keep[10]), (keep[12], keep[13]), (keep[15], keep[16])]
        self.conv_3 = Residual(c1, c2, c3, num_block=4, groups=keep[4], kernel=(3, 3), stride=(1, 1), padding=(1, 1))

        c1 = [(keep[16], keep[17])]
        c2 = [(keep[17], keep[18])]
        c3 = [(keep[18], keep[19])]
        self.conv_34 = Depth_Wise(c1[0], c2[0], c3[0], kernel=(3, 3), stride=(2, 2), padding=(1, 1), groups=keep[19])

        c1 = [(keep[19], keep[20]), (keep[22], keep[23]), (keep[25], keep[26]), (keep[28], keep[29]), (keep[31], keep[32]), (keep[34], keep[35])]
        c2 = [(keep[20], keep[21]), (keep[23], keep[24]), (keep[26], keep[27]), (keep[29], keep[30]), (keep[32], keep[33]), (keep[35], keep[36])]
        c3 = [(keep[21], keep[22]), (keep[24], keep[25]), (keep[27], keep[28]), (keep[30], keep[31]), (keep[33], keep[34]), (keep[36], keep[37])]
        self.conv_4 = Residual(c1, c2, c3, num_block=6, groups=keep[19], kernel=(3, 3), stride=(1, 1), padding=(1, 1))

        c1 = [(keep[37], keep[38])]
        c2 = [(keep[38], keep[39])]
        c3 = [(keep[39], keep[40])]
        self.conv_45 = Depth_Wise(c1[0], c2[0], c3[0], kernel=(3, 3), stride=(2, 2), padding=(1, 1), groups=keep[40])

        c1 = [(keep[40], keep[41]), (keep[43], keep[44])]
        c2 = [(keep[41], keep[42]), (keep[44], keep[45])]
        c3 = [(keep[42], keep[43]), (keep[45], keep[46])]
        self.conv_5 = Residual(c1, c2, c3, num_block=2, groups=keep[40], kernel=(3, 3), stride=(1, 1), padding=(1, 1))

        self.conv_6_sep = Conv_block(keep[46], keep[47], kernel=(1, 1), stride=(1, 1), padding=(0, 0))
        self.conv_6_dw = Linear_block(keep[47], keep[48], groups=keep[48], kernel=conv6_kernel, stride=(1, 1), padding=(0, 0))
        self.conv_6_flatten = Flatten()

        self.linear = nn.Linear(512, embedding_size, bias=False)
        self.bn = nn.BatchNorm1d(embedding_size)
        self.drop = nn.Dropout(p=drop_p)
        self.prob = nn.Linear(embedding_size, num_classes, bias=False)

    def forward(self, x):
        out = self.conv1(x)
        out = self.conv2_dw(out)

        out = self.conv_23(out)
        out = self.conv_3(out)

        out = self.conv_34(out)
        out = self.conv_4(out)

        out = self.conv_45(out)
        out = self.conv_5(out)

        out = self.conv_6_sep(out)
        out = self.conv_6_dw(out)
        out = self.conv_6_flatten(out)

        if self.embedding_size != 512:
            out = self.linear(out)

        out = self.bn(out)
        out = self.drop(out)
        out = self.prob(out)
        return out


# Channel configurations from the original repo
keep_dict = {
    '1.8M': [32, 32, 103, 103, 64, 13, 13, 64, 26, 26, 64, 13, 13, 64, 52, 52, 64, 231, 231, 128, 154, 154, 128, 52, 52, 128, 26, 26, 128, 52, 52, 128, 26, 26, 128, 26, 26, 128, 308, 308, 128, 26, 26, 128, 26, 26, 128, 512, 512],
    '1.8M_': [32, 32, 103, 103, 64, 13, 13, 64, 13, 13, 64, 13, 13, 64, 13, 13, 64, 231, 231, 128, 231, 231, 128, 52, 52, 128, 26, 26, 128, 77, 77, 128, 26, 26, 128, 26, 26, 128, 308, 308, 128, 26, 26, 128, 26, 26, 128, 512, 512],
    # V1SE configuration (from Silent-Face-Anti-Spoofing repo)
    # Based on error analysis, V1SE uses '1.8M' config, not '1.8M_'
    'V1SE': [32, 32, 103, 103, 64, 13, 13, 64, 26, 26, 64, 13, 13, 64, 52, 52, 64, 231, 231, 128, 154, 154, 128, 52, 52, 128, 26, 26, 128, 52, 52, 128, 26, 26, 128, 26, 26, 128, 308, 308, 128, 26, 26, 128, 26, 26, 128, 512, 512]
}


def MiniFASNetV2(embedding_size=128, conv6_kernel=(7, 7), drop_p=0.2, num_classes=3, img_channel=3):
    return MiniFASNet(keep_dict['1.8M_'], embedding_size, conv6_kernel, drop_p, num_classes, img_channel)


def MiniFASNetV1SE(embedding_size=128, conv6_kernel=(7, 7), drop_p=0.0, num_classes=3, img_channel=3):
    # V1SE uses the '1.8M' configuration
    return MiniFASNet(keep_dict['1.8M'], embedding_size, conv6_kernel, drop_p, num_classes, img_channel)


def convert_to_onnx(model_name="V2"):
    """
    Convert MiniFASNet PyTorch checkpoint to ONNX.
    
    Args:
        model_name: "V2" or "V1SE"
    """
    if model_name == "V2":
        pth_path = MODELS_DIR / "2.7_80x80_MiniFASNetV2.pth"
        onnx_path = MODELS_DIR / "2.7_80x80_MiniFASNetV2.onnx"
        model = MiniFASNetV2(embedding_size=128, conv6_kernel=(5, 5), drop_p=0.2, num_classes=3)
    elif model_name == "V1SE":
        pth_path = MODELS_DIR / "4_0_0_80x80_MiniFASNetV1SE.pth"
        onnx_path = MODELS_DIR / "4_0_0_80x80_MiniFASNetV1SE.onnx"
        # V1SE uses drop_p=0.0 and same conv6_kernel for 80x80
        model = MiniFASNetV1SE(embedding_size=128, conv6_kernel=(5, 5), drop_p=0.0, num_classes=3)
    else:
        print(f"ERROR: Unknown model name: {model_name}. Use 'V2' or 'V1SE'")
        sys.exit(1)
    
    if not pth_path.exists():
        print(f"ERROR: Model not found at {pth_path}")
        sys.exit(1)
    
    print(f"Loading model from: {pth_path}")
    
    # Load weights
    state_dict = torch.load(pth_path, map_location="cpu", weights_only=False)
    
    # Handle different state dict formats
    if "state_dict" in state_dict:
        state_dict = state_dict["state_dict"]
    
    # Remove 'module.' prefix if present (from DataParallel)
    new_state_dict = {}
    for k, v in state_dict.items():
        name = k.replace("module.", "")
        new_state_dict[name] = v
    
    # Load weights
    missing, unexpected = model.load_state_dict(new_state_dict, strict=False)
    if missing:
        print(f"Warning: Missing keys: {missing[:5]}..." if len(missing) > 5 else f"Warning: Missing keys: {missing}")
    if unexpected:
        print(f"Warning: Unexpected keys: {unexpected[:5]}..." if len(unexpected) > 5 else f"Warning: Unexpected keys: {unexpected}")
    
    model.eval()
    
    # Create dummy input (batch=1, channels=3, height=80, width=80)
    dummy_input = torch.randn(1, 3, 80, 80)
    
    # Test forward pass
    print("Testing forward pass...")
    with torch.no_grad():
        output = model(dummy_input)
        print(f"Output shape: {output.shape}")
    
    print(f"Exporting to ONNX: {onnx_path}")
    
    # Use legacy exporter to avoid onnxscript compatibility issues
    torch.onnx.export(
        model,
        dummy_input,
        str(onnx_path),
        export_params=True,
        opset_version=11,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={
            "input": {0: "batch_size"},
            "output": {0: "batch_size"},
        },
        dynamo=False,  # Use legacy exporter
    )
    
    print(f"Successfully exported to: {onnx_path}")
    print(f"File size: {onnx_path.stat().st_size / 1024:.1f} KB")
    
    # Verify the ONNX model
    try:
        import onnx
        onnx_model = onnx.load(str(onnx_path))
        onnx.checker.check_model(onnx_model)
        print("ONNX model verification: PASSED")
    except ImportError:
        print("Note: Install 'onnx' package to verify the exported model")
    except Exception as e:
        print(f"ONNX verification warning: {e}")


if __name__ == "__main__":
    import sys
    # Default to V1SE if no argument, or use command line arg
    model_name = sys.argv[1] if len(sys.argv) > 1 else "V1SE"
    convert_to_onnx(model_name)

