#!/bin/sh
#
set -e

MOD="actdif_12"



for i in $MOD
do
python ncats_parse.py ncats_cbc.ini $i.out $i.1
#python ncats_parse.py ncats_rpr.ini $i.out $i.1
#python ncats_parse.py ncats_chol.ini $i.out $i.1
#python ncats_parse.py ncats_alb.ini $i.out $i.1
#python ncats_parse.py ncats_rausecase.ini $i.out $i.1
#python ncats_parse.py ncats_rdw.ini $i.out $i.1


sed -e '/Not reportable/d' <$i.1> $i.11

xform $i.11 $i.2 /home/mars/saulmi2/OCR/cbmi/who/ncats.tab "@%-s"  back "|" 1
xform $i.2 $i.3 /home/mars/saulmi2/OCR/cbmi/who/ncats2.tab "@%-s"  back "|" 1
xform $i.3 $i.4 /home/mars/saulmi2/OCR/cbmi/who/ncats3.tab "@%-s"  back "|" 1

grep @ $i.4 >$i.5
cut -c11-220 <$i.5> $i.6


#xform $i.11 $i.2 /home/mars/saulmi2/OCR/cbmi/who/ncats.tab "%-s"  replace "|" 1
#xform $i.2 $i.3 /home/mars/saulmi2/OCR/cbmi/who/ncats2.tab "%-s"  replace "|" 1
#xform $i.3 $i.lab_deid /home/mars/saulmi2/OCR/cbmi/who/ncats3.tab "%-s"  replace "|" 1

sed -e '/|HMC|/d' <$i.6> tm.$i
mv tm.$i $i.lab_deid
/bin/rm -f $i.1
/bin/rm -f $i.11
/bin/rm -f $i.2
/bin/rm -f $i.3
done


exit 0



