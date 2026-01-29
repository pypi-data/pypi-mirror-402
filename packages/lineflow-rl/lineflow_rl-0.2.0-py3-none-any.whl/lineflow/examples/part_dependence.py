from lineflow.simulation import (
    WorkerPool,
    Source,
    Sink,
    Line,
    Process,
)


class PartDependentProcessLine(Line):
    def build(self):
        source = Source(
            name='Source',
            processing_time=10,
            position=(100, 200),
            unlimited_carriers=True,
            carrier_capacity=1,
            carrier_min_creation=10,
            carrier_specs={
                'Type_A': {
                    'Part1': {
                        'P1': {'extra_processing_time': 20}, 
                        'P2': {'extra_processing_time': 0}
                        }
                },
                'Type_B': {
                    'Part1': {
                        'P1': {'extra_processing_time': 0}, 
                        'P2': {'extra_processing_time': 20}
                    }
                },
            },
        )

        pool = WorkerPool(name='Pool', n_workers=4)

        p1 = Process('P1', processing_time=10, position=(350, 200), worker_pool=pool)
        p2 = Process('P2', processing_time=10, position=(700, 200), worker_pool=pool)
        sink = Sink('Sink', position=(850, 200))

        p1.connect_to_input(source, capacity=15)
        p2.connect_to_input(p1, capacity=15)
        sink.connect_to_input(p2)


if __name__ == '__main__':
    line = PartDependentProcessLine(realtime=True, factor=0.8)
    line.run(simulation_end=1000, visualize=True)
