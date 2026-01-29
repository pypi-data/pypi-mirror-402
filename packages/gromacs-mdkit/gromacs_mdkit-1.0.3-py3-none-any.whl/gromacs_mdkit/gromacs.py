#!/usr/bin/env python3
# mdkit.py - 分子动力学预处理工具
import os
import sys
import subprocess
from pathlib import Path
from rich.console import Console
import periodictable
import math
import readline

class MDKit:
    def __init__(self):
        self.console = Console()
        self.CREATOR_INFO = "[bold blue]Created by Pengcheng Li[/bold blue]"
        self.current_box_length = None  # 存储当前盒子长度
        readline.set_completer(self.complete_file)
        readline.parse_and_bind("tab: complete")

        # 内置模板文件内容
        self.EM_TEMPLATE = """; Minimization
integrator               = cg            ; conjugate gradient algorithm
dt                       = 0.001         ; 1 fs
nsteps                   = 100000        ; 
emtol                    = 100           ; 
emstep                   = 0.01          ; 

; Output control
nstxout                  = 100           ; save coordinates every 100 fs
nstlog                   = 50            ; update log file every 50 fs
nstenergy                = 10            ; save energies every 10 ps

; Neighbor searching
cutoff-scheme            = verlet        ; 
pbc                      = xyz           ; 

; Electrostatics and Van der Waals
coulombtype              = PME           ; Particle-Mesh Ewald
rcoulomb                 = 1.2           ; short-range electrostatic cutoff (nm)
vdwtype                  = cut-off       ; 
rvdw                     = 1.2           ; short-range van der Waals cutoff (nm)
DispCorr                 = EnerPres      ; long-range dispersion corrections
"""

        self.NPT_TEMPLATE = """; NPT
; Run parameters
integrator               = md            ; leap-frog integrator
dt                       = 0.001         ; 1 fs
nsteps                   = 20000000      ; 20 ns

; Output control
nstxout                  = 50000         ; save coordinates every 100 ps
nstvout                  = 50000         ; save velocities every 100 ps
nstenergy                = 50000         ; save energies every 100 ps
nstlog                   = 50000         ; update log file every 100 ps
nstxout-compressed       = 50000         ;
compressed-x-precision   = 1000          ;

; Neighbor searching
cutoff-scheme            = verlet        ; 
ns-type                  = Grid          ;
nstlist                  = 10            ; 10 fs
pbc                      = xyz           ; 

; Electrostatics and Van der Waals
coulombtype              = PME           ; Particle-Mesh Ewald
rcoulomb                 = 1.2           ; short-range electrostatic cutoff (nm)
pme_order                = 4             ; cubic interpolation
fourierspacing           = 0.12          ; grid spacing for FFT
vdwtype                  = cut-off       ; 
rvdw                     = 1.2           ; short-range van der Waals cutoff (nm)
DispCorr                 = EnerPres      ; long-range dispersion corrections

; Temperature coupling
tcoupl                   = nose-hoover   ;   
tc-grps                  = system        ; 
tau-t                    = 1             ; time constant (ps)
ref-t                    = 298           ; reference temperature (K)

; Pressure coupling
Pcoupl                   = Berendsen     ;  
pcoupltype               = isotropic     ;
tau_p                    = 1             ; time constant (ps)
compressibility          = 4.5e-05       ;
ref_p                    = 1.0           ; reference pressure (bar)

; Velocity generation
gen-vel                  = Yes           ; 
gen-temp                 = 298           ; 
gen-seed                 = -1            ; 

; Bond parameters
constraints              = h-bonds       ;      
constraint-algorithm     = lincs         ;
continuation             = no            ;
lincs-iter               = 1             ;
lincs-order              = 4             ;
"""

    def complete_file(self, text, state):
        """文件路径自动补全"""
        files = [f for f in os.listdir('.') if f.startswith(text)]
        return files[state] if state < len(files) else None

    def clear_screen(self):
        """清屏（跨平台）"""
        os.system('cls' if sys.platform.startswith('win') else 'clear')

    def main_menu(self):
        """主菜单 - 简化版，只包含GROMACS预处理功能"""
        self.clear_screen()
        self.console.print(f"[bold cyan]=========  GROMACS Preprocess  =========[/bold cyan]")
        self.console.print(self.CREATOR_INFO)
        self.console.print("[bold cyan]========================================[/bold cyan]")
        self.console.print("1) 构建模拟盒子并生成拓扑文件")
        self.console.print("2) 生成Gromacs的预平衡参数（em.mdp）文件")
        self.console.print("3) 生成Gromacs的模拟参数（npt.mdp）文件")
        self.console.print("4) 执行Gromacs预平衡操作")
        self.console.print("5) 生成Gromacs的模拟（npt.tpr）文件")
        self.console.print("0) 退出")
        self.console.print("[bold cyan]========================================[/bold cyan]")
        return input("输入选项: ")

    @staticmethod
    def calculate_molecular_weight(pdb_file):
        """计算单个分子的质量"""
        total_mass = 0.0
        with open(pdb_file, 'r') as f:
            for line in f:
                if line.startswith(('ATOM', 'HETATM')):
                    element_symbol = line[76:78].strip()
                    try:
                        element = getattr(periodictable, element_symbol)
                        total_mass += element.mass
                    except AttributeError:
                        print(f"Warning: Unknown element {element_symbol} in {pdb_file}")
        return total_mass

    def calculate_total_mass(self, pdb_files, num_molecules):
        """计算体系总质量"""
        total_mass = 0.0
        for pdb_file, num in zip(pdb_files, num_molecules):
            molecular_weight = self.calculate_molecular_weight(pdb_file)
            total_mass += molecular_weight * num
        return total_mass

    def calculate_box_size(self, pdb_files, num_molecules, target_density):
        """计算模拟盒子尺寸"""
        total_mass = self.calculate_total_mass(pdb_files, num_molecules)
        total_mass_g = total_mass * 1.66053906660e-24
        volume_cm3 = total_mass_g / target_density
        volume_ang3 = volume_cm3 / 1e-24
        box_length = volume_ang3 ** (1/3)
        return [math.ceil(box_length / 10) * 10] * 3

    def get_pdb_file(self, filename):
        """获取PDB文件路径，自动添加.pdb后缀"""
        if not filename.lower().endswith('.pdb'):
            filename += '.pdb'
        return filename

    def build_box_and_topology(self):
        """整合功能：构建模拟盒子并生成拓扑文件"""
        self.console.print("\n[bold]==== 构建模拟盒子并生成拓扑文件 ====[/bold]")
        pdb_files, num_molecules = [], []
        
        # 收集分子信息
        self.console.print("\n[bold yellow]注意：请按顺序输入分子，直接按回车结束输入[/bold yellow]")
        molecule_count = 0
        while True:
            molecule_count += 1
            molecule_name = input(f"输入第{molecule_count}个分子名称（不含.pdb后缀）: ").strip()
            
            # 直接按回车结束输入
            if molecule_name == "":
                if molecule_count == 1:
                    self.console.print("[red]错误: 未输入任何分子[/red]")
                    return
                break
            
            molecule_file = self.get_pdb_file(molecule_name)
            if not Path(molecule_file).exists():
                self.console.print(f"[red]错误: 文件 {molecule_file} 不存在[/red]")
                molecule_count -= 1
                continue
            
            num = int(input(f"输入 {molecule_name} 的分子数量: "))
            pdb_files.append(molecule_file)
            num_molecules.append(num)

        # 1. 构建模拟盒子
        self.console.print("\n[bold]--- 构建模拟盒子 ---[/bold]")
        target_density = float(input("输入目标密度(g/cm³): "))
        box_size = self.calculate_box_size(pdb_files, num_molecules, target_density)
        self.current_box_length = box_size[0]  # 保存盒子长度
        box_length = box_size[0]
        self.console.print(f"[green]盒子大小: {box_length:.2f} Å³[/green]")

        output_pdb = input("输入输出PDB文件名(如system): ").strip()
        output_pdb = self.get_pdb_file(output_pdb)
        
        # 生成packmol输入文件 - 保持分子顺序
        with open("packmol.inp", "w") as f:
            f.write(f"tolerance 2.0\nfiletype pdb\noutput {output_pdb}\n\n")
            for pdb, num in zip(pdb_files, num_molecules):
                f.write(f"""structure {pdb}
    number {num}
    inside box 0 0 0 {box_length} {box_length} {box_length}
end structure\n\n""")

        try:
            # 修正后的Packmol调用方式
            if sys.platform.startswith('win'):
                # Windows系统
                with open("packmol.inp", 'r') as f:
                    result = subprocess.run(
                        ["packmol"],
                        stdin=f,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        shell=True
                    )
            else:
                # Linux/Mac系统
                result = subprocess.run(
                    ["packmol < packmol.inp"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    shell=True
                )
            
            if result.returncode == 0:
                self.console.print(f"[green]构建成功: {output_pdb}[/green]")
                if result.stdout:
                    self.console.print(f"[blue]Packmol输出:\n{result.stdout}[/blue]")
            else:
                self.console.print(f"[red]Packmol执行失败: {result.stderr}[/red]")
                return
                
        except FileNotFoundError:
            self.console.print("[red]错误: 未找到Packmol程序，请确保Packmol已安装并添加到系统路径中！[/red]")
            return
        except Exception as e:
            self.console.print(f"[red]错误: {str(e)}[/red]")
            return

        # 2. 生成拓扑文件 - 确保与Packmol相同的分子顺序
        self.console.print("\n[bold]--- 生成拓扑文件 ---[/bold]")
        
        # 按输入顺序收集ITP文件
        itp_files = []
        atp_itp_files = []
        
        for pdb_file in pdb_files:
            base_name = Path(pdb_file).stem
            
            # 检查ATP ITP文件
            atp_itp = f"{base_name}_ATP.itp"
            if Path(atp_itp).exists():
                atp_itp_files.append(atp_itp)
                self.console.print(f"[green]找到ATP ITP文件: {atp_itp}[/green]")
            else:
                self.console.print(f"[yellow]未找到ATP ITP文件: {atp_itp}[/yellow]")
            
            # 检查普通ITP文件
            normal_itp = f"{base_name}.itp"
            if Path(normal_itp).exists():
                itp_files.append(normal_itp)
                self.console.print(f"[green]找到普通ITP文件: {normal_itp}[/green]")
            else:
                self.console.print(f"[yellow]未找到普通ITP文件: {normal_itp}[/yellow]")

        # 构建top文件内容 - 保持分子顺序
        top_content = """[ defaults ]
; nbfunc  comb-rule   gen-pairs  fudgeLJ  fudgeQQ
    1       3           yes        0.5      0.5

; Include topology
"""
        # 添加ITP文件引用 - 按分子顺序
        if atp_itp_files:
            top_content += "\n; ATP ITP files\n"
            for itp in atp_itp_files:
                top_content += f'#include "{itp}"\n'
        
        if itp_files:
            top_content += "\n; Normal ITP files\n"
            for itp in itp_files:
                top_content += f'#include "{itp}"\n'
        
        top_content += "\n[ system ]\n; Name\n"
        
        system_name = input("输入系统名称(如LP40): ").strip()
        top_content += f"{system_name}\n\n[molecules]\n; Compound  #mols\n"

        # 添加分子部分 - 严格保持与Packmol相同的顺序
        for pdb, num in zip(pdb_files, num_molecules):
            mol_name = Path(pdb).stem
            top_content += f"{mol_name}  {num}\n"

        output_top = input("输入输出拓扑文件名(如topol.top): ").strip()
        with open(output_top, 'w') as f:
            f.write(top_content)
        
        # 显示顺序确认信息
        self.console.print("\n[bold cyan]分子顺序确认:[/bold cyan]")
        for i, (pdb, num) in enumerate(zip(pdb_files, num_molecules), 1):
            mol_name = Path(pdb).stem
            self.console.print(f"  {i}. {mol_name}: {num}个分子")
        
        self.console.print(f"\n[green]拓扑文件已生成: {output_top}[/green]")
        self.console.print("[yellow]请确认分子顺序与您的预期一致![/yellow]")
        
        self.console.print(f"\n[bold green]✓ 完成！已生成:[/bold green]")
        self.console.print(f"[green]- 模拟盒子: {output_pdb}[/green]")
        self.console.print(f"[green]- 拓扑文件: {output_top}[/green]")
        self.console.print("[bold green]分子顺序已确保一致![/bold green]")

    def generate_em_mdp(self):
        """生成能量最小化参数文件"""
        self.console.print("\n[bold]==== 生成em.mdp文件 ====[/bold]")
        output_file = input("输入输出文件名(如em.mdp): ").strip()
        
        with open(output_file, 'w') as f:
            f.write(self.EM_TEMPLATE)
        
        self.console.print(f"[green]文件已生成: {output_file}[/green]")
        self.console.print("[yellow]请根据实际需求修改参数![/yellow]")

    def generate_npt_mdp(self):
        """生成NPT模拟参数文件"""
        self.console.print("\n[bold]==== 生成npt.mdp文件 ====[/bold]")
        output_file = input("输入输出文件名(如npt.mdp): ").strip()
        
        with open(output_file, 'w') as f:
            f.write(self.NPT_TEMPLATE)
        
        self.console.print(f"[green]文件已生成: {output_file}[/green]")
        self.console.print("[yellow]请根据实际需求修改参数![/yellow]")

    def run_gromacs_em(self):
        """执行GROMACS预平衡"""
        self.console.print("\n[bold]==== 执行GROMACS预平衡 ====[/bold]")
        
        if self.current_box_length is None:
            self.console.print("[red]错误: 请先构建模拟盒子![/red]")
            return
        
        # 获取必要文件路径
        box_pdb_input = input("输入Packmol生成的PDB文件名(如system.pdb): ").strip()
        box_pdb = self.get_pdb_file(box_pdb_input)
        if not Path(box_pdb).exists():
            self.console.print(f"[red]错误: PDB文件 {box_pdb} 不存在![/red]")
            return
            
        top_file = input("输入拓扑文件路径(如topol.top): ").strip()
        if not Path(top_file).exists():
            self.console.print("[red]错误: 拓扑文件不存在![/red]")
            return
            
        em_mdp = input("输入em.mdp文件路径(如em.mdp): ").strip()
        if not Path(em_mdp).exists():
            self.console.print("[red]错误: em.mdp文件不存在![/red]")
            return
        
        # 转换为纳米单位
        box_nm = self.current_box_length / 10.0
        
        try:
            # 1. 运行editconf
            self.console.print("[blue]运行gmx editconf...[/blue]")
            subprocess.run([
                "gmx", "editconf",
                "-f", box_pdb,
                "-o", "box.gro",
                "-bt", "cubic",
                "-box", str(box_nm), str(box_nm), str(box_nm)
            ], check=True)
            
            # 2. 运行grompp
            self.console.print("[blue]运行gmx grompp...[/blue]")
            subprocess.run([
                "gmx", "grompp",
                "-f", em_mdp,
                "-c", "box.gro",
                "-p", top_file,
                "-o", "em.tpr",
                "-maxwarn", "100"
            ], check=True)
            
            # 3. 运行mdrun
            self.console.print("[blue]运行gmx mdrun...[/blue]")
            subprocess.run([
                "gmx", "mdrun",
                "-v",
                "-deffnm", "em"
            ], check=True)
            
            self.console.print("[green]GROMACS预平衡完成![/green]")
            self.console.print("[green]输出文件: em.gro, em.trr, em.edr, em.log[/green]")
            
        except subprocess.CalledProcessError as e:
            self.console.print(f"[red]GROMACS执行错误: {str(e)}[/red]")
        except Exception as e:
            self.console.print(f"[red]错误: {str(e)}[/red]")

    def generate_npt_tpr(self):
        """生成NPT模拟的tpr文件"""
        self.console.print("\n[bold]==== 生成NPT模拟的tpr文件 ====[/bold]")
        
        # 获取必要文件路径
        gro_file_input = input("输入结构文件名(如em.gro): ").strip()
        gro_file = gro_file_input + ".gro" if not gro_file_input.endswith('.gro') else gro_file_input
        if not Path(gro_file).exists():
            self.console.print(f"[red]错误: 结构文件 {gro_file} 不存在![/red]")
            return
            
        top_file = input("输入拓扑文件路径(如topol.top): ").strip()
        if not Path(top_file).exists():
            self.console.print("[red]错误: 拓扑文件不存在![/red]")
            return
            
        npt_mdp = input("输入npt.mdp文件路径(如npt.mdp): ").strip()
        if not Path(npt_mdp).exists():
            self.console.print("[red]错误: npt.mdp文件不存在![/red]")
            return
        
        output_file = input("输入输出文件名(如npt.tpr): ").strip()
        
        try:
            # 运行grompp生成tpr文件
            self.console.print("[blue]运行gmx grompp...[/blue]")
            subprocess.run([
                "gmx", "grompp",
                "-f", npt_mdp,
                "-c", gro_file,
                "-p", top_file,
                "-o", output_file,
                "-maxwarn", "100"
            ], check=True)
            
            self.console.print(f"[green]NPT模拟tpr文件生成成功: {output_file}[/green]")
            
        except subprocess.CalledProcessError as e:
            self.console.print(f"[red]GROMACS执行错误: {str(e)}[/red]")
        except Exception as e:
            self.console.print(f"[red]错误: {str(e)}[/red]")

    def handle_main_menu(self, choice):
        """处理主菜单选择"""
        if choice == '1':
            self.build_box_and_topology()
        elif choice == '2':
            self.generate_em_mdp()
        elif choice == '3':
            self.generate_npt_mdp()
        elif choice == '4':
            self.run_gromacs_em()
        elif choice == '5':
            self.generate_npt_tpr()
        elif choice == '0':
            self.console.print("[bold]再见！[/bold]")
            sys.exit()
        else:
            self.console.print("[red]无效选项![/red]")


def main():
    """命令行入口点"""
    mdkit = MDKit()
    while True:
        try:
            choice = mdkit.main_menu()
            mdkit.handle_main_menu(choice)
            input("\n按Enter继续...")
        except KeyboardInterrupt:
            mdkit.console.print("\n[bold yellow]已退出[/bold yellow]")
            sys.exit()

if __name__ == "__main__":
    main()