import inspect
import torch

from .extension import get_model_info


def export(model, meta=None):
    """
    导出网络结构与参数

    :param model: pytorch模型对象
    :param meta: 为用户提供额外帮助的元数据
    """
    # 【关键】切换到 eval 模式，避免 dropout/bn 状态干扰
    model.eval()
    model._is_full_backward_hook = True
    definition, parameters = get_model_info(model)
    init_inputs = ",".join(parameters[1:])
    torch.save(
        {
            "state_dict": model.state_dict(),
            "definition": definition,
            "init": "model = {}({})".format(model.__class__.__name__, init_inputs),
            "version": torch.__version__,
            "meta": meta,
        },
        model.__class__.__name__ + ".pth",
    )


def load(file, imports, init_inputs, load_state=False):
    """
    加载模型文件

    :param file: pytorch模型文件
    :param imports: 导入的依赖库
    :param local_vars: 初始化参数
    :param load_state: 是否加载预训练权重
    """
    m = torch.load(file, weights_only=False)
    # 定义一个带模块信息的自定义类

    exec(m["definition"], imports)
    exec(m["init"], imports, init_inputs)
    model = init_inputs["model"]
    if load_state:
        model.load_state_dict(m["state_dict"])
    return model
