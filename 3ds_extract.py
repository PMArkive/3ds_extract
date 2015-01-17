import argparse
import os
import subprocess

def run_command(cmd, quiet):
    print cmd
    
    if quiet:
        with open(os.devnull, 'wb') as devnull:
            subprocess.check_call(cmd, stdout=devnull, stderr=subprocess.STDOUT)
    else:
        subprocess.check_call(cmd)
        
    print ""
    
def get_titleid(filename):
    titleid = None
    
    if os.path.exists(filename):    
        with open(filename, "rb") as file:
            file.seek(0x108)
            titleid_raw = file.read(8)[::-1]
            titleid = "".join(["%02x" % ord(c) for c in titleid_raw]).upper()
        
    return titleid

ctrtool_exe = "ctrtool.exe"
padxorer_exe = "padxorer.exe"

parser = argparse.ArgumentParser()
parser.add_argument("romfile", type=str, help=".3ds rom file to extract data from")
parser.add_argument("section", type=str, help="Section to extract", choices=["exefs","romfs", "exheader"])
parser.add_argument("-x", "--xorpad", type=str, default=None, help="xorpad file (Specify if it cannot be found by default)")
parser.add_argument("-n", "--no-cleanup", action="store_true", default=False, help="Keep decrypted data file after extraction?")
parser.add_argument("-q", "--quiet", action="store_true", default=False, help="Hide output from tools")
args = parser.parse_args()

if args.xorpad == None:
    titleid = get_titleid(args.romfile)
    if titleid == None:
        print "Could not get titleid"
        exit(-1)
   
    xorpad_filename = "%s.Main.%s.xorpad" % (titleid, args.section)
    xorpad_filename = os.path.join(os.path.dirname(args.romfile), xorpad_filename)
    if not os.path.exists(xorpad_filename):
        print "Xorpad file %s could not be found. Please specify an xorpad file using -x." % xorpad_filename
        exit(-1)
else:
    xorpad_filename = args.xorpad

rom_basename = os.path.splitext(args.romfile)[0]
output_basename = "%s-%s" % (rom_basename, args.section)
output_filename = "%s.bin" % output_basename

# Step 1: Extract section
print "- Step 1: Extract %s from %s" % (args.section, args.romfile)
exec_str = "%s -x -p --%s=%s %s" % (ctrtool_exe, args.section, output_filename, args.romfile)
run_command(exec_str, args.quiet)

if not os.path.exists(output_filename):
    print "Expected %s but couldn't find it. Was there an error?" % output_filename
    exit(-1)

# Step 2: xor data
print "- Step 2: Xor %s with %s" % (output_filename, xorpad_filename)
exec_str = "%s %s %s" % (padxorer_exe, output_filename, xorpad_filename)
run_command(exec_str, args.quiet)

if os.path.exists(output_filename):
    os.remove(output_filename) # Clean up unneeded file

# Step 3: Extract data
output_decrypted_filename = "%s.out" % output_filename
print "- Step 3: Extract %s" % output_decrypted_filename

if not os.path.exists(output_decrypted_filename):
    print "Expected %s but couldn't find it. Was there an error?" % output_decrypted_filename
    exit(-1)

if args.section == "exheader":
    exec_str = "%s -x -t %s %s" % (ctrtool_exe, args.section, output_decrypted_filename)
elif args.section == "exefs":
    exec_str = "%s -x -t %s --%sdir=%s --decompresscode %s" % (ctrtool_exe, args.section, args.section, output_basename, output_decrypted_filename)
else:
    exec_str = "%s -x -t %s --%sdir=%s %s" % (ctrtool_exe, args.section, args.section, output_basename, output_decrypted_filename)
    
run_command(exec_str, args.quiet)

# Step 4: Clean temporary files
if args.no_cleanup != True:
    print "- Step 4: Clean up temporary file %s" % (output_decrypted_filename)
    if os.path.exists(output_decrypted_filename):
        os.remove(output_decrypted_filename)
    print ""

print "Finished!"