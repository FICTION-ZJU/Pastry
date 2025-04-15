tmout="60s"
opt="-degree 2 -dump-stats"
bin="./absynth"
output="result.doc"

#cp ../../source/absynth .
rm -f ${output}

echo "=====================================" >> ${output}
echo "Linear Programs" 						 >> ${output}
echo "=====================================" >> ${output}
echo "" >> ${output}

for ex in linear/*.imp
do
	echo "------------------------------------" >> ${output}
	echo $(basename "${ex}") 					>> ${output}
	echo "------------------------------------" >> ${output}
	echo "--- Program $(basename "${ex}")"

	gtimeout $tmout $bin $opt $ex >> ${output}
	
	code=$?
	case $code in
	124)
		echo "[TIMEOUT]"
		;;
	0)
		echo "[OK]"
		;;
	*)
		echo "[FAILURE $code]"
		;;
	esac

	echo "" >> ${output}
done

echo "=====================================" >> ${output}
echo "Polynomial Programs" 					 >> ${output}
echo "=====================================" >> ${output}
echo "" >> ${output}

for ex in polynomial/*.imp
do
	echo "------------------------------------" >> ${output}
	echo $(basename "${ex}") 					>> ${output}
	echo "------------------------------------" >> ${output}
	echo "--- Program $(basename "${ex}")"

	gtimeout $tmout $bin $opt $ex >> ${output}
	
	code=$?
	case $code in
	124)
		echo "[TIMEOUT]"
		;;
	0)
		echo "[OK]"
		;;
	*)
		echo "[FAILURE $code]"
		;;
	esac

	echo "" >> ${output}
done

echo "Done."
#rm -f ${bin}
