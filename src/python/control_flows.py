import random
import schemdraw
from schemdraw import flow

from .ir_nodes import id_hash


def create_flows(block, id_func=id_hash):
    flows = {}
    queue = [block]
    while queue:
        cur = queue.pop(0)
        cur_id = id_func(cur)
        if cur_id in flows:
            continue
        queue.extend(cur.deps)
        flows[id_func(cur)] = [id_func(b) for b in cur.deps]
    return flows


class ControlFlows:
    def __init__(self, flows):
        self.flows = flows
        self.colour_parts = ["00", "66", "AB", "FF"]
        self.blocks = {}
        self.dy = -2  # change this value to increase spacing

    def draw_flow(self, display):
        with schemdraw.Drawing(show=display) as self.d:
            self.d.config(fontsize=11)
            flow.Box(w=0, h=0)
            self.d.move(3, 0)

            for block in self.flows.keys():
                self.blocks[block] = flow.Box(w=2, h=1).anchor("N").label(block)
                self.d.move(0, self.dy)

            alt = 2
            for block, branches in self.flows.items():
                colour = "#"
                for i in range(3):
                    colour += random.choice(self.colour_parts)
                if colour == "#FFFFFF":
                    colour = "#000000"
                for end_block in branches:
                    if (alt % 2) == 0:
                        start = self.blocks[block].E
                        end = self.blocks[end_block].E
                        curve = 0.5
                    else:
                        start = self.blocks[block].W
                        end = self.blocks[end_block].W
                        curve = -0.5
                    if start.y < end.y:
                        curve *= -1
                    flow.Arc2(k=curve, arrow="->").at(start).to(end).color(colour)
                alt += 1

    def save_flow(self, path):
        if self.d:
            image_bytes = self.d.get_imagedata("svg")
            with open(path, "wb") as f:
                f.write(image_bytes)


if __name__ == "__main__":
    flows = {'e057': ['6b0b'], '6b0b': ['d003', '28d2'], 'd003': [], '28d2': []}
    a = ControlFlows(flows)
    a.draw_flow()
