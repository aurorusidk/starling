import random
import schemdraw
from schemdraw import flow

from .ir_nodes import id_hash


def create_flows(block):
    flows = {}
    queue = [block]
    while queue:
        cur = queue.pop(0)
        cur_id = id_hash(cur)
        if cur_id in flows:
            continue
        queue.extend(cur.deps)
        flows[id_hash(cur)] = [id_hash(b) for b in cur.deps]
    return flows


class ControlFlows:
    def __init__(self, flows):
        self.flows = flows
        self.colour_parts = ["00", "66", "AB", "FF"]
        self.blocks = {}
        self.dy = -2  # change this value to increase spacing

    def draw_flow(self):
        with schemdraw.Drawing() as d:
            d.config(fontsize=11)
            flow.Box(w=0, h=0)
            d.move(3, 0)

            for block in self.flows.keys():
                self.blocks[block] = flow.Box(w=2, h=1).anchor("N").label(block)
                d.move(0, self.dy)

            alt = 2
            for block, branches in self.flows.items():
                colour = "#"
                for i in range(3):
                    colour += random.choice(self.colour_parts)
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
                    print(start)
                    print(end)
                    flow.Arc2(k=curve, arrow="->").at(start).to(end).color(colour)
                alt += 1


if __name__ == "__main__":
    flows = {'e057': ['6b0b'], '6b0b': ['d003', '28d2'], 'd003': [], '28d2': []}
    a = ControlFlows(flows)
    a.draw_flow()
