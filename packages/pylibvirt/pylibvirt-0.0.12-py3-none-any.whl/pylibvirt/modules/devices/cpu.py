from pylibvirt.modules.devices import Device


class VcpuDevice(Device):
    XML_NAME = "vcpu"

    def __init__(self, vcpu: int, vcpu_args=None):
        super().__init__(name=self.XML_NAME)
        if vcpu_args is None:
            vcpu_args = {'placement': 'static'}
        self.root = []
        self.__vcpu_args = vcpu_args
        self.__vcpu = vcpu
        self.generate_data()

    def generate_data(self):
        self.data.update({
            self.XML_NAME: {
                "attr": self.__vcpu_args,
                "text": str(self.__vcpu)
            }
        })


class CpuDevice(Device):
    XML_NAME = "cpu"

    def __init__(self, vcpu_args: dict or None = None, cpu_model: str = None,
                 model_args=None, cpu_args=None, vcpu: int = 1,
                 topology_args: dict or None =
                 None):
        super().__init__(name=self.XML_NAME)
        if model_args is None:
            model_args = {'fallback': 'allow'}
        if cpu_args is None:
            cpu_args = {'mode': 'host-model', 'check': 'partial'}
        self.root = []
        self.__cpu_model = cpu_model
        self.__cpu_args = cpu_args
        self.__model_args = model_args
        self.__topology = topology_args
        if not self.__topology:
            self.__vcpu = VcpuDevice(vcpu=vcpu, vcpu_args=vcpu_args)
        else:
            self.__vcpu = VcpuDevice(vcpu=self.count_vcpu(), vcpu_args=vcpu_args)
        self.generate_data()

    @property
    def cpu_model(self) -> str:
        return self.__cpu_model

    @cpu_model.setter
    def cpu_model(self, cpu_model: str):
        self.__cpu_model = cpu_model

    @property
    def cpu_args(self) -> dict:
        return self.__cpu_args

    @cpu_args.setter
    def cpu_args(self, cpu_args: str):
        self.__cpu_args = cpu_args

    @property
    def topology(self):
        if not self.__topology:
            return False
        elif 'sockets' not in self.__topology or 'cores' not in self.__topology or \
                'threads' not in self.__topology:
            return False
        else:
            return self.__topology

    def count_vcpu(self):
        return self.topology['sockets'] * self.topology['cores'] * self.topology[
            'threads']

    def generate_data(self):
        self.data.update({
            self.XML_NAME: {
                "attr": self.cpu_args
            }
        })
        if self.cpu_model:
            self.data[self.XML_NAME].update({"children": {
                "model": {
                    "text": self.cpu_model,
                    "attr": self.__model_args
                }
            }})
        self.data.update(self.__vcpu.data)
