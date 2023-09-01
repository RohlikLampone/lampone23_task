use rand::Rng;
use serde::{Deserialize, Serialize};
use std::fs::File;
use std::io::Read;
use std::time::{Duration, Instant};


const TEST_PATHS: i32 = 5_000_000; // Set the desired number of test paths
const MAX_STEPS: i32 = 64; // Set the maximum number of steps in a path
const TIME_TO_RUN_FOR: u128 = 60_000; // number of milliseconds to run for before returing the result

#[derive(Debug, Serialize, Deserialize)]
struct Data {
    map: [[i32; 8]; 8],
    start: (usize, usize),
    finish: (usize, usize),
    start_dir: i32,
}


fn path_to_lrfb(path: &Vec<(usize, usize)>, start_dir: i32) -> String {
    let mut dir = start_dir;
    let mut lrfb = String::new();

    for x in 0..(path.len() - 1) {
        let next_dir: i32;
        if path[x].0 > path[x + 1].0 {
            next_dir = 0;
        } else if path[x].1 < path[x + 1].1 {
            next_dir = 1;
        } else if path[x].0 < path[x + 1].0 {
            next_dir = 2;
        } else if path[x].1 > path[x + 1].1 {
            next_dir = 3;
        } else {
            // this never happens anyway
            panic!()
        }

        if next_dir > dir {
            lrfb += &"R".repeat((next_dir - dir) as usize);
        } else if next_dir < dir {
            lrfb += &"L".repeat((dir - next_dir) as usize);
        }

        lrfb = lrfb.replace("RRR", "L");
        lrfb = lrfb.replace("LLL", "R");

        dir = next_dir;

        lrfb += "F";
    }

    lrfb
}


fn normalize_and_generate_probability(num1: f64, num2: f64, num3: f64, num4: f64) -> usize {
    // Normalize the numbers
    let total = num1 + num2 + num3 + num4;
    let normalized_nums = [num1 / total, num2 / total, num3 / total, num4 / total];

    // Generate a random number between 0 and 1
    let mut rng = rand::thread_rng();
    let rand_num: f64 = rng.gen();

    // Determine the range for each number
    let ranges = [
        normalized_nums[0],
        normalized_nums[0] + normalized_nums[1],
        1.0 - normalized_nums[3],
        1.0,
    ];

    // Find which range the random number falls into
    for i in 0..4 {
        if rand_num < ranges[i] {
            return i; // between 0 and 4 (excludes 4)
        }
    }

    unreachable!(); // This should never be reached
}


fn main() -> Result<(), Box<dyn std::error::Error>> {

    // start measuring time
    let time = Instant::now();

    let file = File::open("data.json")?;
    let mut contents = String::new();
    let mut file_reader = std::io::BufReader::new(file);
    file_reader.read_to_string(&mut contents)?;

    let data: Data = serde_json::from_str(&contents)?;

    let mut map = data.map;
    let start = data.start;
    let finish = data.finish;
    let start_dir = data.start_dir;

    let mut best_path: Vec<(usize,usize)> = Vec::new();
    let mut best_path_points = -100000000;
    let mut paths_tested = 0;

    let mut rng = rand::thread_rng();

    while TEST_PATHS > paths_tested || best_path.is_empty() {
        paths_tested += 1;
        let mut current_path: Vec<(usize,usize)> = vec![start];
        let mut current_path_points = 0;
        let mut current_map = map.clone();
        let mut visited_map = [[1.;8];8];
        let mut current_pos = start;
        let repeat_strictness = rng.gen::<f64>();//.powi(1);
        let point_strictness = rng.gen::<f64>();//.powi(1);

        for _ in 0..MAX_STEPS {

            let u:f64 = if current_pos.1 > 0 {
                (1.0 + f64::tanh(point_strictness * current_map[current_pos.0][current_pos.1 - 1] as f64))
                *
                (visited_map[current_pos.0][current_pos.1 - 1])
            } else {
                0.0
            };

            let r = if current_pos.0 < 7 {
                (1.0 + f64::tanh(point_strictness * current_map[current_pos.0 + 1][current_pos.1] as f64))
                *
                (visited_map[current_pos.0 + 1][current_pos.1])
            } else {
                0.0
            };

            let d = if current_pos.1 < 7 {
                (1.0 + f64::tanh(point_strictness * current_map[current_pos.0][current_pos.1 + 1] as f64))
                *
                (visited_map[current_pos.0][current_pos.1 + 1])
            } else {
                0.0
            };

            let l = if current_pos.0 > 0 {
                (1.0 + f64::tanh(point_strictness * current_map[current_pos.0 - 1][current_pos.1] as f64))
                *
                (visited_map[current_pos.0 - 1][current_pos.1])
            } else {
                0.0
            };
            
            let rand_dir = normalize_and_generate_probability(u, r, d, l);

            if rand_dir == 0 {
                current_pos.1 -= 1;
                current_path_points += current_map[current_pos.0][current_pos.1];
                current_path.push(current_pos);
            }
                
            else if rand_dir == 1 {
                current_pos.0 += 1;
                current_path_points += current_map[current_pos.0][current_pos.1];
                current_path.push(current_pos);
            }
            
            else if rand_dir == 2 {
                current_pos.1 += 1;
                current_path_points += current_map[current_pos.0][current_pos.1];
                current_path.push(current_pos);
            }
            
            else if rand_dir == 3 {
                current_pos.0 -= 1;
                current_path_points += current_map[current_pos.0][current_pos.1];
                current_path.push(current_pos);
            }
            
            if current_map[current_pos.0][current_pos.1] > 0 {
                current_map[current_pos.0][current_pos.1] = 0;
            }
            visited_map[current_pos.0][current_pos.1] *= repeat_strictness;
            
            if current_pos == finish {
                let current_path_points_final = current_path_points - current_path.len() as i32+1;
                if current_path_points_final >= best_path_points {
                    best_path = current_path.clone();
                    best_path_points = current_path_points_final;
                }
            }
        }
        if Instant::now().checked_duration_since(time).unwrap().as_millis() > TIME_TO_RUN_FOR {
            break
        }
    }

    println!("{}", best_path_points);
    println!("{}", path_to_lrfb(&best_path, start_dir));

    Ok(())
}
