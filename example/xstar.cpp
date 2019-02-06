#include <fstream>
#include <iostream>

#include <boost/functional/hash.hpp>
#include <boost/program_options.hpp>

#include <yaml-cpp/yaml.h>

#include <libMultiRobotPlanning/xstar.hpp>
#include "timer.hpp"

using libMultiRobotPlanning::Neighbor;
using libMultiRobotPlanning::PlanResult;
using libMultiRobotPlanning::XStar;

struct State {
  State(int time, int x, int y) : time(time), x(x), y(y) {}

  bool operator==(const State& s) const {
    return time == s.time && x == s.x && y == s.y;
  }

  bool equalExceptTime(const State& s) const { return x == s.x && y == s.y; }

  friend std::ostream& operator<<(std::ostream& os, const State& s) {
    return os << s.time << ": (" << s.x << "," << s.y << ")";
    // return os << "(" << s.x << "," << s.y << ")";
  }

  int time;
  int x;
  int y;
};

namespace std {
template <>
struct hash<State> {
  size_t operator()(const State& s) const {
    size_t seed = 0;
    boost::hash_combine(seed, s.time);
    boost::hash_combine(seed, s.x);
    boost::hash_combine(seed, s.y);
    return seed;
  }
};
}  // namespace std

///
enum class Action {
  Up,
  Down,
  Left,
  Right,
  Wait,
};

std::ostream& operator<<(std::ostream& os, const Action& a) {
  switch (a) {
    case Action::Up:
      os << "Up";
      break;
    case Action::Down:
      os << "Down";
      break;
    case Action::Left:
      os << "Left";
      break;
    case Action::Right:
      os << "Right";
      break;
    case Action::Wait:
      os << "Wait";
      break;
  }
  return os;
}

///

struct Conflict {
  enum Type {
    Vertex,
    Edge,
  };

  int time;
  size_t agent1;
  size_t agent2;
  Type type;

  int x1;
  int y1;
  int x2;
  int y2;

  friend std::ostream& operator<<(std::ostream& os, const Conflict& c) {
    switch (c.type) {
      case Vertex:
        return os << c.time << ": Vertex(" << c.x1 << "," << c.y1 << ")";
      case Edge:
        return os << c.time << ": Edge(" << c.x1 << "," << c.y1 << "," << c.x2
                  << "," << c.y2 << ")";
    }
    return os;
  }
};

// namespace std {
// template <>
// struct hash<Window> {
//   size_t operator()(const Window& w) const {
//     size_t seed = 0;
//     boost::hash_combine(seed, w.min_state);
//     boost::hash_combine(seed, w.max_state);
//     return seed;
//   }
// };
// }  // namespace std

struct Location {
  Location(int x, int y) : x(x), y(y) {}
  int x;
  int y;

  bool operator<(const Location& other) const {
    return std::tie(x, y) < std::tie(other.x, other.y);
  }

  bool operator==(const Location& other) const {
    return std::tie(x, y) == std::tie(other.x, other.y);
  }

  friend std::ostream& operator<<(std::ostream& os, const Location& c) {
    return os << "(" << c.x << "," << c.y << ")";
  }
};

namespace std {
template <>
struct hash<Location> {
  size_t operator()(const Location& s) const {
    size_t seed = 0;
    boost::hash_combine(seed, s.x);
    boost::hash_combine(seed, s.y);
    return seed;
  }
};
}  // namespace std

using Time_t = int;

struct Window {
  Location min_position;
  Location max_position;
  Time_t min_t;
  std::vector<size_t> agent_idxs;

  Window() : min_position(0, 0), max_position(0, 0) {}

  Window(const Location& min_position, const Location& max_position,
         const std::vector<size_t>& agent_idxs,
         const std::vector<PlanResult<State, Action, int>>& joint_plan)
      : min_position(min_position),
        max_position(max_position),
        min_t(std::numeric_limits<Time_t>::max()),
        agent_idxs(agent_idxs) {
    std::sort(this->agent_idxs.begin(), this->agent_idxs.end());
    setMinT(joint_plan);
  }

  Window merge(
      const Window& o,
      const std::vector<PlanResult<State, Action, int>>& joint_plan) const {
    int min_x = std::min(min_position.x, o.min_position.x);
    int max_x = std::max(max_position.x, o.max_position.x);
    int min_y = std::min(min_position.y, o.min_position.y);
    int max_y = std::max(max_position.y, o.max_position.y);

    auto joined_agent_idxs = agent_idxs;
    joined_agent_idxs.insert(joined_agent_idxs.end(), o.agent_idxs.begin(),
                             o.agent_idxs.end());
    std::sort(joined_agent_idxs.begin(), joined_agent_idxs.end());
    const auto it =
        std::unique(joined_agent_idxs.begin(), joined_agent_idxs.end());
    joined_agent_idxs.resize(std::distance(joined_agent_idxs.begin(), it));

    return {{min_x, min_y}, {max_x, max_y}, joined_agent_idxs, joint_plan};
  }

  bool contains(const Location& s, const size_t& agent_idx) const {
    if (find(agent_idxs.begin(), agent_idxs.end(), agent_idx) ==
        agent_idxs.end()) {
      return false;
    }
    return (s.x >= min_position.x && s.y <= max_position.y &&
            s.y >= min_position.y && s.y <= min_position.y);
  }

  friend std::ostream& operator<<(std::ostream& os, const Window& w) {
    os << "Min: " << w.min_position << " Max: " << w.max_position
       << " Agents: ";
    for (const auto& e : w.agent_idxs) {
      os << e << " ";
    }
    return os;
  }

 private:
  void setMinT(const std::vector<PlanResult<State, Action, int>>& joint_plan) {
    for (const size_t& agent_idx : agent_idxs) {
      const PlanResult<State, Action, int>& individual_plan =
          joint_plan.at(agent_idx);
      for (const auto& pair : individual_plan.states) {
        const State& s = pair.first;
        if (s.time >= min_t) {
          break;
        }

        if (this->contains({s.y, s.y}, agent_idx)) {
          if (min_t > s.time) {
            min_t = s.time;
          }
          break;
        }
      }
    }
  }
};

///
class Environment {
 public:
  Environment(size_t dimx, size_t dimy, std::unordered_set<Location> obstacles,
              std::vector<Location> goals)
      : m_dimx(dimx),
        m_dimy(dimy),
        m_obstacles(std::move(obstacles)),
        m_goals(std::move(goals)),
        m_agentIdx(0),
        m_highLevelExpanded(0),
        m_lowLevelExpanded(0) {
    // computeHeuristic();
  }

  Environment(const Environment&) = delete;
  Environment& operator=(const Environment&) = delete;

  void setLowLevelContext(size_t agentIdx) { m_agentIdx = agentIdx; }

  int admissibleHeuristic(const State& s) {
    // std::cout << "H: " <<  s << " " << m_heuristic[m_agentIdx][s.x + m_dimx *
    // s.y] << std::endl;
    // return m_heuristic[m_agentIdx][s.x + m_dimx * s.y];
    return std::abs(s.x - m_goals[m_agentIdx].x) +
           std::abs(s.y - m_goals[m_agentIdx].y);
  }

  bool isSolution(const State& s) {
    return s.x == m_goals[m_agentIdx].x && s.y == m_goals[m_agentIdx].y;
  }

  void getWindowNeighbors(
      const State& s, const size_t agent_idx, const Window& w,
      const std::vector<PlanResult<State, Action, int>>& joint_plan,
      std::vector<Neighbor<State, Action, int>>& in_window_neighbors,
      std::vector<Neighbor<State, Action, int>>& out_window_neighbors) {
    if (!w.contains({s.x, s.y}, agent_idx)) {
      // If the given state is not in the window but it falls along the path
      // into the window, add the next step in the path towards the window.
      if (getState(agent_idx, joint_plan, s.time) == s) {
        in_window_neighbors.emplace_back(
            getStateAsNeighbor(agent_idx, joint_plan, s.time + 1));
      }
      return;
    }

    std::vector<Neighbor<State, Action, int>> neighbors;
    getNeighbors(s, neighbors);
    for (auto& n : neighbors) {
      if (w.contains({n.state.x, n.state.y}, agent_idx)) {
        in_window_neighbors.emplace_back(std::move(n));
      } else {
        out_window_neighbors.emplace_back(std::move(n));
      }
    }
  }

  void getNeighbors(const State& s,
                    std::vector<Neighbor<State, Action, int>>& neighbors) {
    // std::cout << "#VC " << constraints.vertexConstraints.size() << std::endl;
    // for(const auto& vc : constraints.vertexConstraints) {
    //   std::cout << "  " << vc.time << "," << vc.x << "," << vc.y <<
    //   std::endl;
    // }
    neighbors.clear();
    {
      State n(s.time + 1, s.x, s.y);
      if (stateValid(n) && transitionValid(s, n)) {
        neighbors.emplace_back(
            Neighbor<State, Action, int>(n, Action::Wait, 1));
      }
    }
    {
      State n(s.time + 1, s.x - 1, s.y);
      if (stateValid(n) && transitionValid(s, n)) {
        neighbors.emplace_back(
            Neighbor<State, Action, int>(n, Action::Left, 1));
      }
    }
    {
      State n(s.time + 1, s.x + 1, s.y);
      if (stateValid(n) && transitionValid(s, n)) {
        neighbors.emplace_back(
            Neighbor<State, Action, int>(n, Action::Right, 1));
      }
    }
    {
      State n(s.time + 1, s.x, s.y + 1);
      if (stateValid(n) && transitionValid(s, n)) {
        neighbors.emplace_back(Neighbor<State, Action, int>(n, Action::Up, 1));
      }
    }
    {
      State n(s.time + 1, s.x, s.y - 1);
      if (stateValid(n) && transitionValid(s, n)) {
        neighbors.emplace_back(
            Neighbor<State, Action, int>(n, Action::Down, 1));
      }
    }
  }

  bool getFirstConflict(
      const std::vector<PlanResult<State, Action, int>>& solution,
      Conflict& result) {
    int max_t = 0;
    for (const auto& sol : solution) {
      max_t = std::max<int>(max_t, sol.states.size() - 1);
    }

    for (int t = 0; t < max_t; ++t) {
      // check drive-drive vertex collisions
      for (size_t i = 0; i < solution.size(); ++i) {
        State state1 = getState(i, solution, t);
        for (size_t j = i + 1; j < solution.size(); ++j) {
          State state2 = getState(j, solution, t);
          if (state1.equalExceptTime(state2)) {
            result.time = t;
            result.agent1 = i;
            result.agent2 = j;
            result.type = Conflict::Vertex;
            result.x1 = state1.x;
            result.y1 = state1.y;
            // std::cout << "VC " << t << "," << state1.x << "," << state1.y <<
            // std::endl;
            return true;
          }
        }
      }
      // drive-drive edge (swap)
      for (size_t i = 0; i < solution.size(); ++i) {
        State state1a = getState(i, solution, t);
        State state1b = getState(i, solution, t + 1);
        for (size_t j = i + 1; j < solution.size(); ++j) {
          State state2a = getState(j, solution, t);
          State state2b = getState(j, solution, t + 1);
          if (state1a.equalExceptTime(state2b) &&
              state1b.equalExceptTime(state2a)) {
            result.time = t;
            result.agent1 = i;
            result.agent2 = j;
            result.type = Conflict::Edge;
            result.x1 = state1a.x;
            result.y1 = state1a.y;
            result.x2 = state1b.x;
            result.y2 = state1b.y;
            return true;
          }
        }
      }
    }

    return false;
  }

  Window createWindowFromConflict(
      const Conflict& conflict,
      const std::vector<PlanResult<State, Action, int>>& joint_plan) {
    static constexpr int kInitialRadius = 2;
    switch (conflict.type) {
      case Conflict::Type::Edge: {
        std::cout << "Type: Edge"
                  << " x1: " << conflict.x1 << " y1: " << conflict.y1
                  << " x2: " << conflict.x2 << " y2: " << conflict.y2
                  << " time: " << conflict.time
                  << " Agents: " << conflict.agent1 << ", " << conflict.agent2
                  << '\n';
        int min_x = std::min(conflict.x1, conflict.x2) - kInitialRadius;
        int max_x = std::max(conflict.x1, conflict.x2) + kInitialRadius;
        int min_y = std::min(conflict.y1, conflict.y2) - kInitialRadius;
        int max_y = std::max(conflict.y1, conflict.y2) + kInitialRadius;
        Location min_state(min_x, min_y);
        Location max_state(max_x, max_y);
        return {min_state,
                max_state,
                {conflict.agent1, conflict.agent2},
                joint_plan};
      }
      case Conflict::Type::Vertex: {
        std::cout << "Type: Vertex"
                  << " x1: " << conflict.x1 << " y1: " << conflict.y1
                  << " time: " << conflict.time
                  << " Agents: " << conflict.agent1 << ", " << conflict.agent2
                  << '\n';
        int min_x = conflict.x1 - kInitialRadius;
        int max_x = conflict.x1 + kInitialRadius;
        int min_y = conflict.y1 - kInitialRadius;
        int max_y = conflict.y1 + kInitialRadius;
        Location min_state(min_x, min_y);
        Location max_state(max_x, max_y);
        return {min_state,
                max_state,
                {conflict.agent1, conflict.agent2},
                joint_plan};
      }
    }
  }

  void onExpandHighLevelNode(int /*cost*/) { m_highLevelExpanded++; }

  void onExpandLowLevelNode(const State& /*s*/, int /*fScore*/,
                            int /*gScore*/) {
    m_lowLevelExpanded++;
  }

  int highLevelExpanded() { return m_highLevelExpanded; }

  int lowLevelExpanded() const { return m_lowLevelExpanded; }

 private:
  Neighbor<State, Action, int> getStateAsNeighbor(
      size_t agentIdx,
      const std::vector<PlanResult<State, Action, int>>& solution, size_t t) {
    assert(agentIdx < solution.size());
    if (t < solution[agentIdx].states.size()) {
      assert(solution[agentIdx].states[t].first.time == static_cast<int>(t));
      const auto& sc = solution[agentIdx].states[t];
      const Action a = solution[agentIdx].actions[t].first;
      return {sc.first, a, sc.second};
    }
    assert(!solution[agentIdx].states.empty());
    const auto& sc = solution[agentIdx].states.back();
    const Action a = solution[agentIdx].actions.back().first;
    return {sc.first, a, sc.second};
  }

  State getState(size_t agentIdx,
                 const std::vector<PlanResult<State, Action, int>>& solution,
                 size_t t) {
    assert(agentIdx < solution.size());
    if (t < solution[agentIdx].states.size()) {
      assert(solution[agentIdx].states[t].first.time == static_cast<int>(t));
      return solution[agentIdx].states[t].first;
    }
    assert(!solution[agentIdx].states.empty());
    return solution[agentIdx].states.back().first;
  }

  bool stateValid(const State& s) {
    return s.x >= 0 && s.x < m_dimx && s.y >= 0 && s.y < m_dimy &&
           m_obstacles.find(Location(s.x, s.y)) == m_obstacles.end();
  }

  bool transitionValid(const State& s1, const State& s2) { return true; }

 private:
  int m_dimx;
  int m_dimy;
  std::unordered_set<Location> m_obstacles;
  std::vector<Location> m_goals;
  // std::vector< std::vector<int> > m_heuristic;
  size_t m_agentIdx;
  int m_highLevelExpanded;
  int m_lowLevelExpanded;
};

int main(int argc, char* argv[]) {
  namespace po = boost::program_options;
  // Declare the supported options.
  po::options_description desc("Allowed options");
  std::string inputFile;
  std::string outputFile;
  desc.add_options()("help", "produce help message")(
      "input,i", po::value<std::string>(&inputFile)->required(),
      "input file (YAML)")("output,o",
                           po::value<std::string>(&outputFile)->required(),
                           "output file (YAML)");

  try {
    po::variables_map vm;
    po::store(po::parse_command_line(argc, argv, desc), vm);
    po::notify(vm);

    if (vm.count("help") != 0u) {
      std::cout << desc << "\n";
      return 0;
    }
  } catch (po::error& e) {
    std::cerr << e.what() << std::endl << std::endl;
    std::cerr << desc << std::endl;
    return 1;
  }

  YAML::Node config = YAML::LoadFile(inputFile);

  std::unordered_set<Location> obstacles;
  std::vector<Location> goals;
  std::vector<State> startStates;

  const auto& dim = config["map"]["dimensions"];
  int dimx = dim[0].as<int>();
  int dimy = dim[1].as<int>();

  for (const auto& node : config["map"]["obstacles"]) {
    obstacles.insert(Location(node[0].as<int>(), node[1].as<int>()));
  }

  for (const auto& node : config["agents"]) {
    const auto& start = node["start"];
    const auto& goal = node["goal"];
    startStates.emplace_back(State(0, start[0].as<int>(), start[1].as<int>()));
    // std::cout << "s: " << startStates.back() << std::endl;
    goals.emplace_back(Location(goal[0].as<int>(), goal[1].as<int>()));
  }

  Environment mapf(dimx, dimy, obstacles, goals);
  XStar<State, Action, int, Conflict, Window, Environment> cbs(mapf);
  std::vector<PlanResult<State, Action, int>> solution;

  Timer timer;
  bool success = cbs.search(startStates, solution);
  timer.stop();

  if (success) {
    std::cout << "Planning successful! " << std::endl;
    int cost = 0;
    int makespan = 0;
    for (const auto& s : solution) {
      cost += s.cost;
      makespan = std::max<int>(makespan, s.cost);
    }

    std::ofstream out(outputFile);
    out << "statistics:" << std::endl;
    out << "  cost: " << cost << std::endl;
    out << "  makespan: " << makespan << std::endl;
    out << "  runtime: " << timer.elapsedSeconds() << std::endl;
    out << "  highLevelExpanded: " << mapf.highLevelExpanded() << std::endl;
    out << "  lowLevelExpanded: " << mapf.lowLevelExpanded() << std::endl;
    out << "schedule:" << std::endl;
    for (size_t a = 0; a < solution.size(); ++a) {
      // std::cout << "Solution for: " << a << std::endl;
      // for (size_t i = 0; i < solution[a].actions.size(); ++i) {
      //   std::cout << solution[a].states[i].second << ": " <<
      //   solution[a].states[i].first << "->" << solution[a].actions[i].first
      //   << "(cost: " << solution[a].actions[i].second << ")" << std::endl;
      // }
      // std::cout << solution[a].states.back().second << ": " <<
      // solution[a].states.back().first << std::endl;

      out << "  agent" << a << ":" << std::endl;
      for (const auto& state : solution[a].states) {
        out << "    - x: " << state.first.x << std::endl
            << "      y: " << state.first.y << std::endl
            << "      t: " << state.second << std::endl;
      }
    }
  } else {
    std::cout << "Planning NOT successful!" << std::endl;
  }

  return 0;
}
