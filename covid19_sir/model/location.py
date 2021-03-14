from model.base import (AgentBase, SimulationState, flip_coin, get_parameters, unique_id, random_selection, beta_range,
                        logger)
from model.utils import RestaurantType


class Location(AgentBase):
    def __init__(self, covid_model, strid_prefix, strid_suffix):
        super().__init__(unique_id(), covid_model)
        self.custom_parameters = {}
        self.humans = []
        self.locations = []
        self.container = None
        self.spreading_rate = get_parameters().get('spreading_rate')
        self.strid = strid_prefix
        if strid_prefix != '':
            self.strid += '-'
        self.strid += type(self).__name__
        if strid_suffix != '':
            self.strid += '-' + strid_suffix

    def get_parameter(self, key):
        if key in self.custom_parameters:
            return self.custom_parameters[key]
        return get_parameters().get(key)

    def set_custom_parameters(self, s, args):
        for key in args:
            # Only parameters in s (defined in constructor of super) can
            # be overwritten
            check = False
            for k, v in s:
                if k == key:
                    check = True
            assert check
        self.custom_parameters = {}
        for key, value in s:
            self.custom_parameters[key] = args.get(key, value)

    def move_to(self, human, target):
        if human in self.humans:
            self.humans.remove(human)
            target.humans.append(human)

    def step(self):
        super().step()

    def check_spreading(self, h1, h2):
        #print(f"check-spreading in location {self.unique_id} of types {type(self).mro()}")
        if h1.is_infected():
            logger().debug(f"Check to see if {h1} can infect {h2} in {self}")
            if h1.is_contagious() and not h2.is_infected():
                logger().debug(f"contagion_probability = {self.get_parameter('contagion_probability')}")
                if flip_coin(self.get_parameter('contagion_probability')):
                    me = self.get_parameter('mask_efficacy')
                    if not h1.is_wearing_mask() or (h1.is_wearing_mask() and not flip_coin(me)):
                        if h2.strid not in self.covid_model.global_count.infection_info:
                            self.covid_model.global_count.infection_info[h2.strid] = self
                        logger().debug(f"Infection succeeded - {h1} has infected {h2} in {self} with contagion "
                                       f"probability {self.get_parameter('contagion_probability')}")

                        h1.count_infected_humans += 1
                        h2.infect(self)
                    else:
                        if h1.is_wearing_mask():
                            logger().debug(f"Infection failed - infector {h1} wearing mask")
                        if h2.is_wearing_mask():
                            logger().debug(f"Infection failed - infectee {h2} wearing mask")
                else:
                    logger().debug(f"Infection failed - {self} didn't pass contagion_probability check with contagion "
                                   f"probability {self.get_parameter('contagion_probability')}")
            else:
                if not h1.is_contagious():
                    logger().debug(f"Infection failed - infector {h1} is not contagious")
                if h2.is_infected():
                    logger().debug(f"Infection failed - infectee {h2} is already infected")

    def spread_infection(self):
        if len(self.humans) > 0:
            logger().info(f"{self} is spreading infection amongst {len(self.humans)} humans")
        for h1 in self.humans:
            if h1.is_infected() and not h1.is_hospitalized() and not h1.is_isolated():
                for h2 in self.humans:
                    if h1 != h2:
                        self.check_spreading(h1, h2)


class BuildingUnit(Location):
    def __init__(self, capacity, covid_model, strid_prefix, strid_suffix, **kwargs):
        super().__init__(covid_model, strid_prefix, strid_suffix)
        self.set_custom_parameters([
            ('contagion_probability', 0.0)
        ], kwargs)
        self.capacity = capacity
        self.allocation = []

    def step(self):
        super().step()
        if self.covid_model.current_state == SimulationState.MORNING_AT_HOME or \
                self.covid_model.current_state == SimulationState.MAIN_ACTIVITY:
            self.spread_infection()


class HomogeneousBuilding(Location):
    def __init__(self, building_capacity, covid_model, strid_prefix, strid_suffix, **kwargs):
        super().__init__(covid_model, strid_prefix, strid_suffix)
        self.unit_args = kwargs
        self.capacity = building_capacity
        self.allocation = {}

    def get_unit(self, human):
        return self.allocation[human]

class Hospital(HomogeneousBuilding):
    # n: number of co-workers each worker interacts with during a day of work
    # r: (r * TOTAL_NUMBER_OF_PATIENTS_IN_THE_HOSPITAL) is approx the number of patients each worker
    #    interacts with during a day of work
    def __init__(self, n, r, covid_model, strid_prefix, strid_suffix, contagion_probability, **kwargs):
        inf = 10000
        super().__init__(inf, covid_model, strid_prefix, strid_suffix, **kwargs)
        self.patients = []
        self.patient_interaction_rate = r
        for i in range(inf):
            self.locations.append(BuildingUnit(n + 1, covid_model, strid_prefix, f"hospital-unit-{i}",
                                  contagion_probability=contagion_probability))

    def spread_infection(self):
        if len(self.patients) > 0:
            logger().info(f"{self} is spreading infection patients -> workers")
            print(f"{self} is spreading infection patients -> workers")
            for worker in humans:
                for patient in patients:
                    if not flip_coin(r):
                        continue
                    logger().debug(f"Check to see if patient {patient} can infect worker {worker} in {self}")
                    print(f"Check to see if patient {patient} can infect worker {worker} in {self}")
                    if not worker.is_infected():
                        logger().debug(f"contagion_probability = {self.get_parameter('contagion_probability')}")
                        if flip_coin(self.get_parameter('contagion_probability')):
                            if worker.strid not in self.covid_model.global_count.infection_info:
                                self.covid_model.global_count.infection_info[worker.strid] = self
                            logger().debug(f"Infection succeeded - {patient} has infected {worker} in {self} with contagion "
                                           f"probability {self.get_parameter('contagion_probability')}")
                            print(f"Infection succeeded - {patient} has infected {worker} in {self} with contagion "
                                  f"probability {self.get_parameter('contagion_probability')}")
                            patient.count_infected_humans += 1
                            worker.infect(patient)
                        else:
                            logger().debug(f"Infection failed - {self} didn't pass contagion_probability check with contagion "
                                           f"probability {self.get_parameter('contagion_probability')}")
                            print(f"Infection failed - {self} didn't pass contagion_probability check with contagion "
                                  f"probability {self.get_parameter('contagion_probability')}")
                    else:
                        logger().debug(f"Infection failed - infectee {worker} is already infected")
                        print(f"Infection failed - infectee {worker} is already infected")
        super().spread_infection() # amongst workers only

class Restaurant(Location):
    def __init__(self, capacity, restaurant_type, is_outdoor, covid_model, strid_prefix, strid_suffix, **kwargs):
        super().__init__(covid_model, strid_prefix, strid_suffix)
        outdoor = True
        indoor = False
        # https://docs.google.com/document/d/1imCNXOyoyecfD_sVNmKpmbWVB6xqP-FWlHELAyOg1Vs/edit
        base_fast_food = beta_range(0.014, 0.1)  # normal_ci(0.014, 0.1, 10)
        base_fancy = beta_range(0.07, 0.2)  # normal_ci(0.07, 0.2, 10)
        base_bar = beta_range(0.174, 0.796)  # normal_ci(0.174, 0.796, 10)
        cp = {
            RestaurantType.FAST_FOOD: {
                indoor: base_fast_food,
                outdoor: base_fast_food / 2
            },
            RestaurantType.FANCY: {
                indoor: base_fancy,
                outdoor: base_fancy / 2
            },
            RestaurantType.BAR: {
                indoor: base_bar,
                outdoor: base_bar / 2
            }
        }
        self.capacity = capacity
        self.available = capacity
        self.restaurant_type = restaurant_type
        self.is_outdoor = is_outdoor
        self.set_custom_parameters([
            ('contagion_probability', cp[restaurant_type][is_outdoor])
        ], kwargs)

    def spread_infection(self):
        if len(self.humans) > 0:
            logger().info(f"{self} is spreading infection amongst {len(self.humans)} humans")
        for h1 in self.humans:
            for h2 in self.humans:
                if h1 != h2:
                    if h1.social_event == h2.social_event or \
                            flip_coin(0.25 * self.get_parameter('allowed_restaurant_capacity')):
                        self.check_spreading(h1, h2)

    def step(self):
        super().step()
        capacity = self.get_parameter('allowed_restaurant_capacity')
        ci = {1.0: (0.19, 1.23), 0.5: (0.11, 0.74), 0.25: (0.08, 0.50)}
        # https://docs.google.com/document/d/1imCNXOyoyecfD_sVNmKpmbWVB6xqP-FWlHELAyOg1Vs/edit
        lb, ub = ci[capacity]
        self.spreading_rate = beta_range(lb, ub)  # normal_ci(lb, ub, 20)
        if self.covid_model.current_state == SimulationState.POST_WORK_ACTIVITY:
            self.spread_infection()


class District(Location):
    def __init__(self, name, covid_model, strid_prefix, strid_suffix,home_district_list=[], **kwargs):
        super().__init__(covid_model, strid_prefix, strid_suffix)
        self.allocation = {}
        self.name = name
        self.debug = False
        self.home_district_list = home_district_list

    def get_buildings(self, human):
        if human in self.allocation:
            return self.allocation[human]
        return []

    def get_available_hospital(self):
        for location in self.locations:
            if isinstance(location, Hospital):
                return location
        return None

    def get_available_restaurant(self, people_count, outdoor, restaurant_type,favorites):
        #print ("favorites")
        #print (favorites)
        #for location in self.locations:
        for location in favorites:
            #print("location.strid")
            #print (location.strid)
            #print(isinstance(location, Restaurant))
            #print(location.restaurant_type == restaurant_type))
            #print(location.is_outdoor == outdoor)
            #print(        ((location.capacity - location.available) + people_count) <= \
                    #location.capacity * self.get_parameter('allowed_restaurant_capacity') )
            if isinstance(location, Restaurant) and \
                    location.restaurant_type == restaurant_type and \
                    location.is_outdoor == outdoor and \
                    ((location.capacity - location.available) + people_count) <= \
                    location.capacity * self.get_parameter('allowed_restaurant_capacity'): 
                return location
        logger().info("No restaurant is available")
        return None

    def move_to(self, human, target):
        s = self.get_buildings(human)[0].get_unit(human)
        if isinstance(target, District):
            t = target.get_buildings(human)[0].get_unit(human)
        else:
            t = target
        s.move_to(human, t)

    def move_from(self, human, source):
        t = self.get_buildings(human)[0].get_unit(human)
        if isinstance(source, District):
            s = source.get_buildings(human)[0].get_unit(human)
        else:
            s = source
        s.move_to(human, t)

    def _select(self, building_type, n, same_unit, exclusive):
        count = 0
        while True:
            count += 1
            assert count < (len(self.locations) * 1000)  # infinite loop
            building = random_selection(self.locations)
            if not isinstance(building, building_type):
                continue
            for unit in building.locations:
                if exclusive:
                    if not unit.allocation:
                        return building, unit
                else:
                    vacancy = unit.capacity - len(unit.allocation)
                    if vacancy >= n or vacancy == 1 and not same_unit:
                        return building, unit

    def _select_different_unit(self, building, invalid_unit):
        for unit in building.locations:
            if unit != invalid_unit and len(unit.allocation) < unit.capacity:
                return unit
        assert False

    def _debug(self):
        super()._debug()

    def allocate(self, humans, same_building=False, same_unit=False, exclusive=False,
                 building_type=HomogeneousBuilding):
        assert (exclusive and same_unit and same_building) or \
               (not exclusive and same_unit and same_building) or \
               (not exclusive and not same_unit and same_building) or \
               (not exclusive and not same_unit and not same_building)
        building = None
        unit = None
        for human in humans:
            if building is None or (building is not None and not same_building):
                building, unit = self._select(building_type, len(humans), same_unit, exclusive)
            else:
                if not same_unit:
                    unit = self._select_different_unit(building, unit)
            if human not in self.allocation:
                self.allocation[human] = []
            self.allocation[human].append(building)
            building.allocation[human] = unit
            unit.allocation.append(human)

    def __repr__(self):
        txt = f"\n{self.name} district with {len(self.locations)} Buildings\n"
        district_total_humans = 0
        for building in self.locations:
            if len(building.locations) > 0:
                txt = txt + f"{type(building).__name__}: {building.capacity} units (each with capacity for " \
                            f"{building.locations[0].capacity} people.) "
            else:
                txt = txt + f"{type(building).__name__}: {building.capacity} units with no locations"
            sum_allocated = 0
            total_allocated = 0
            for unit in building.locations:
                if unit.allocation:
                    total_allocated += 1
                    sum_allocated += len(unit.allocation)
            txt = txt + f"{total_allocated} allocated units with a total of {sum_allocated} people.\n"
            district_total_humans += sum_allocated
        txt = txt + f"Total of {district_total_humans} people allocated in this district.\n"
        return txt


